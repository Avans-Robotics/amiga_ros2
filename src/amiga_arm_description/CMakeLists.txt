cmake_minimum_required(VERSION 3.8)
project(amiga_arm_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config fields launch rviz urdf DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/pick_carrot.py DESTINATION lib/${PROJECT_NAME})

ament_package()
