cmake_minimum_required(VERSION 3.16)
project(case022_thermostat_sensor_decoupling LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(case022_lib
  src/thermostat_controller.cc
  src/tmp26_sensor.cc
)
target_include_directories(case022_lib PUBLIC src)

add_executable(case022_app app/main.cc)
target_link_libraries(case022_app PRIVATE case022_lib)
