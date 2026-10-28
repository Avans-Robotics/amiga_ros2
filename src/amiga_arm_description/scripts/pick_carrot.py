#!/usr/bin/env python3
"""Pick one carrot of a pixelfield Field with the simulated Lite 6 (sideways mount, Gripper Lite).

Oracle, no perception and no MoveIt: the carrot comes from the Field's manifest.json, the robot
pose from Gazebo, the joint angles from a small IK on the robot_description.

  pick_carrot.py spawn <manifest.json>   print the carrot and the launch args to spawn next to it
  pick_carrot.py pick <manifest.json>    reach it, close the gripper on its leaf bunch, lift

`pick` prints what the Plant did (/world/pixelfield/pixelfield/pull_out) and exits 0 once the
Plant was picked (pulled out or not), 1 if it never was. See docs/simulation.md.
"""
import argparse
import atexit
import json
import re
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

GRIP_HEIGHT = 0.04   # m, finger pad centre above the crown: the leaf bunch fits the open fingers
PAD_ABOVE_TCP = 0.0126  # m, finger pad centre above link_tcp (fingertip end) with the tool down
MIN_BUNCH = 0.025    # m, thinner bunches slip through the closed Gripper Lite (22.4 mm pad gap)
REACH_X = -0.65      # m, carrot in base_footprint x: middle of the top-down reach of the sideways arm
APPROACH = 0.20      # m, pre-grasp above the grip point, over the leaves
LIFT_MARGIN = 0.05   # m, lifted past the root length: pixelfield detaches the root after that
OPEN, CLOSED = 0.0089, 0.0  # finger_joint1, see sim_controllers.yaml
JOINTS = [f'joint{i}' for i in range(1, 7)]


def choose(manifest_path):
    """The carrot nearest the Field's east edge whose leaf bunch the gripper can squeeze."""
    from pixelfield import ROOT
    from pixelfield.exporters.gazebo import gripper
    manifest = json.loads(Path(manifest_path).read_text())
    gripper.GRIP_HEIGHT, gripper.JAW_MARGIN = GRIP_HEIGHT, 0.0
    best = None
    for p in manifest['plants']:
        if p['crop'] != 'carrot':
            continue
        lib = manifest['crops']['carrot']['library']
        physics = json.loads((ROOT / lib / p['variant']).with_suffix('.physics.json').read_text())
        if gripper.jaw_width(physics, p['scale']) < MIN_BUNCH:
            continue
        root = next(link for link in physics['links'] if link['name'] == 'root')
        z = [v[2] for v in root['hull']['vertices']]
        crown, root_length = max(z) * p['scale'], (max(z) - min(z)) * p['scale']
        if best is None or p['pose']['x'] > best[0]['pose']['x']:
            best = (p, crown, root_length)
    if best is None:
        raise SystemExit(f'no carrot in {manifest_path} with a leaf bunch of {MIN_BUNCH * 1000:.0f} mm')
    return best


def spawn_pose(plant):
    """Heading east with the carrot REACH_X behind base_footprint: wheels and chassis off the Field."""
    return plant['pose']['x'] - REACH_X, plant['pose']['y'], 0.0


# --- kinematics -------------------------------------------------------------------------------

def rpy_matrix(r, p, y):
    cr, sr, cp, sp, cy, sy = np.cos(r), np.sin(r), np.cos(p), np.sin(p), np.cos(y), np.sin(y)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


class Chain:
    """base_footprint to link_tcp from a URDF string."""

    def __init__(self, urdf, tip='link_tcp', base='base_footprint'):
        joints = {j.find('child').get('link'): j for j in ET.fromstring(urdf).findall('joint')}
        self.chain, link = [], tip
        while link != base:
            self.chain.insert(0, joints[link])
            link = joints[link].find('parent').get('link')
        self.limits = np.array([[float(j.find('limit').get(k)) for k in ('lower', 'upper')]
                                for j in self.chain if j.get('type') == 'revolute'])

    def fk(self, q):
        m, i = np.eye(4), 0
        for j in self.chain:
            o = j.find('origin')
            t = np.eye(4)
            t[:3, :3] = rpy_matrix(*[float(v) for v in o.get('rpy', '0 0 0').split()])
            t[:3, 3] = [float(v) for v in o.get('xyz', '0 0 0').split()]
            m = m @ t
            if j.get('type') == 'revolute':
                a = np.array([float(v) for v in j.find('axis').get('xyz').split()])
                k = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
                r = np.eye(4)
                r[:3, :3] = np.eye(3) + np.sin(q[i]) * k + (1 - np.cos(q[i])) * k @ k
                m, i = m @ r, i + 1
        return m

    def ik(self, p, q0):
        """Joint angles with link_tcp at p and its z axis pointing down: from q0 if that
        converges, else the solution closest to q0 from random starts."""
        def err(q):
            m = self.fk(q)
            return np.concatenate([p - m[:3, 3], 0.3 * (m[:3, 2] - [0, 0, -1])])  # tool down, not up

        def solve(q):
            for _ in range(200):
                e = err(q)
                if np.linalg.norm(e) < 1e-5:
                    return q
                jac = np.array([(err(q + d) - e) / 1e-6 for d in np.eye(6) * 1e-6]).T
                q = np.clip(q - jac.T @ np.linalg.solve(jac @ jac.T + 1e-4 * np.eye(6), e),
                            self.limits[:, 0], self.limits[:, 1])
            return None
        q0 = np.array(q0, dtype=float)
        q = solve(q0)
        if q is not None:
            return q
        rng = np.random.default_rng(0)
        found = [q for q in (solve(rng.uniform(*self.limits.T)) for _ in range(30)) if q is not None]
        if not found:
            raise RuntimeError(f'no IK solution for {np.round(p, 3)}')
        # same pose, nearest to q0: a joint a full turn away takes the wrist the long way round
        wrapped = [q0 + (q - q0 + np.pi) % (2 * np.pi) - np.pi for q in found]
        found = [w if np.all((w >= self.limits[:, 0]) & (w <= self.limits[:, 1])) else q
                 for w, q in zip(wrapped, found)]
        return min(found, key=lambda q: np.abs(q - q0).sum())

    def line(self, a, b, q0, n=10):
        """IK along the straight line a to b: a joint path that keeps the tool vertical."""
        path = []
        for t in np.linspace(0, 1, n + 1)[1:]:
            q0 = self.ik(a + t * (b - a), q0)
            path.append(q0)
        return path


# --- ROS and Gazebo -------------------------------------------------------------------------

def robot_pose(model='amiga_arm', world='pixelfield'):
    """x, y, yaw of the spawned model from Gazebo (oracle)."""
    out = subprocess.run(['gz', 'model', '-m', model, '-p'], capture_output=True, text=True,
                         timeout=20).stdout
    xyz, rpy = (np.array(v.split(), dtype=float) for v in re.findall(r'\[([-\d.e ]+)\]', out)[-2:])
    return xyz[0], xyz[1], rpy[2]


def pull_out_events(pid, world='pixelfield'):
    """Follow the pull-out state of Plant pid in a thread; returns its events list and peaks."""
    # ponytail: gz CLI instead of the gz Python bindings, whose subscriber lost the nested
    # gz.msgs.Pose class in this process ("No message class registered").
    events, peak = [], {'d': 0.0, 'force': 0.0}
    echo = subprocess.Popen(['gz', 'topic', '-e', '--json-output', '-t',
                             f'/world/{world}/pixelfield/pull_out'], stdout=subprocess.PIPE, text=True)
    atexit.register(echo.terminate)  # also when pick fails: a left gz echo keeps the shell waiting

    def follow():
        for line in echo.stdout:
            params = json.loads(line).get('params', {})
            if params.get('plant', {}).get('stringValue') != pid:
                continue
            peak['d'] = max(peak['d'], params.get('d', {}).get('doubleValue', 0.0))
            peak['force'] = max(peak['force'], params.get('force', {}).get('doubleValue', 0.0))
            if 'event' in params:
                events.append(params['event']['stringValue'])
                print(f'  {pid}: {events[-1]}', flush=True)
    threading.Thread(target=follow, daemon=True).start()
    return events, peak


def pick(args):
    import rclpy
    import rclpy.duration
    import rclpy.parameter
    from control_msgs.action import FollowJointTrajectory
    from rclpy.action import ActionClient
    from rclpy.qos import DurabilityPolicy, QoSProfile
    from sensor_msgs.msg import JointState
    from std_msgs.msg import Float64MultiArray, String
    from trajectory_msgs.msg import JointTrajectoryPoint

    plant, crown, root_length = choose(args.manifest)
    pid = plant['id']
    events, peak = pull_out_events(pid)

    rclpy.init()
    node = rclpy.create_node('pick_carrot', parameter_overrides=[
        rclpy.parameter.Parameter('use_sim_time', value=True)])
    urdf, joints = [], {}
    node.create_subscription(String, '/robot_description', lambda m: urdf.append(m.data),
                             QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
    node.create_subscription(JointState, '/joint_states',
                             lambda m: joints.update(zip(m.name, m.position)), 10)
    grip = node.create_publisher(Float64MultiArray, '/gripper_controller/commands', 10)
    arm = ActionClient(node, FollowJointTrajectory, '/lite6_traj_controller/follow_joint_trajectory')
    while not (urdf and all(j in joints for j in JOINTS)):
        rclpy.spin_once(node, timeout_sec=0.1)
    arm.wait_for_server()
    chain = Chain(urdf[0])

    def gripper(position, seconds):
        end = time.time() + seconds  # wall time: keep publishing until the fingers had time to move
        while time.time() < end:
            grip.publish(Float64MultiArray(data=[position]))
            rclpy.spin_once(node, timeout_sec=0.1)

    def move(path, seconds):
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = JOINTS
        for i, q in enumerate(path, 1):
            t = seconds * i / len(path)
            goal.trajectory.points.append(JointTrajectoryPoint(
                positions=list(q), time_from_start=rclpy.duration.Duration(seconds=t).to_msg()))
        handle = arm.send_goal_async(goal)
        rclpy.spin_until_future_complete(node, handle)
        result = handle.result().get_result_async()
        rclpy.spin_until_future_complete(node, result)
        if result.result().result.error_code != 0:  # e.g. the lift held back by the carrot
            rclpy.spin_once(node, timeout_sec=0.1)
            print(f'  trajectory: {result.result().result.error_string}; joints '
                  f'{np.round([joints[j] for j in JOINTS], 2)}, goal {np.round(path[-1], 2)}', flush=True)

    x, y, yaw = robot_pose()
    c, s = np.cos(-yaw), np.sin(-yaw)
    dx, dy = plant['pose']['x'] - x, plant['pose']['y'] - y
    grasp = np.array([c * dx - s * dy, s * dx + c * dy, crown + GRIP_HEIGHT - PAD_ABOVE_TCP])
    above = grasp + [0, 0, APPROACH]
    print(f'{pid}: pull-out force {plant["pull_out_force"]:.1f} N, root {root_length:.3f} m, '
          f'grip at {np.round(grasp, 3)} in base_footprint (robot at {x:.3f} {y:.3f} yaw {yaw:.3f})',
          flush=True)

    q = np.array([joints[j] for j in JOINTS])
    q_above = chain.ik(above, q)
    gripper(OPEN, 1.0)
    move([q_above], 5.0)
    down = chain.line(above, grasp, q_above)
    move(down, 4.0)
    gripper(CLOSED, 2.0)
    up = chain.line(grasp, grasp + [0, 0, root_length + LIFT_MARGIN], down[-1])
    move(up, 8.0)
    gripper(CLOSED, 2.0)  # hold, so a slow slip still shows

    outcome = ('pulled out' if 'detached' in events else
               'not pulled out' if 'picked' in events else 'never picked')
    print(f'RESULT {pid}: {outcome}; peak d {peak["d"] * 1000:.1f} mm, peak force '
          f'{peak["force"]:.1f} N; events {events}', flush=True)
    rclpy.shutdown()
    return 0 if 'picked' in events else 1


def check(urdf):
    """Self-check of the IK on a sideways-mount URDF with the gripper: pick_carrot.py check x.urdf"""
    chain = Chain(urdf)
    a = np.array([REACH_X, 0.05, 0.05])
    path = chain.line(a + [0, 0, APPROACH], a, chain.ik(a + [0, 0, APPROACH], np.zeros(6)))
    for q, z in zip(path, np.linspace(a[2] + APPROACH, a[2], 11)[1:]):
        m = chain.fk(q)
        assert np.allclose(m[:3, 3], [a[0], a[1], z], atol=1e-4), m[:3, 3]
        assert m[2, 2] < -0.9999, m[:3, 2]
    print('ik ok')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('mode', choices=['spawn', 'pick', 'check'])
    parser.add_argument('file', help='manifest.json (spawn, pick) or a URDF (check)')
    args = parser.parse_args()
    args.manifest = args.file
    if args.mode == 'check':
        return check(Path(args.file).read_text())
    if args.mode == 'spawn':
        plant, *_ = choose(args.manifest)
        x, y, yaw = spawn_pose(plant)
        print(f'# {plant["id"]} at {plant["pose"]["x"]:.3f} {plant["pose"]["y"]:.3f}', file=sys.stderr)
        print(f'x:={x:.3f} y:={y:.3f} yaw:={yaw}')
        return 0
    return pick(args)


if __name__ == '__main__':
    sys.exit(main())
