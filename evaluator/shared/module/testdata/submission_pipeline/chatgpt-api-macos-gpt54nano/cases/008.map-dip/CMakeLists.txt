cmake_minimum_required(VERSION 3.16)
project(case008_map_dip LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(case008_lib
  src/map_snapshot.cc
  src/providers_builtin.cc
)
target_include_directories(case008_lib PUBLIC
  src
  third_party
  ${CMAKE_SOURCE_DIR}/third_party/json/single_include
)
target_link_libraries(case008_lib PUBLIC nlohmann_json)

add_executable(case008_app app/main.cc)
target_link_libraries(case008_app PRIVATE case008_lib)
