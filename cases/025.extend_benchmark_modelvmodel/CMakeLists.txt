cmake_minimum_required(VERSION 3.16)
project(case025_benchmark_metric_boundary LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(case025_lib
  src/benchmark_data.cc
  src/benchmark_runner.cc
  src/scoreboard.cc
)

target_include_directories(case025_lib PUBLIC src)

add_executable(case025_app app/main.cc)
target_link_libraries(case025_app PRIVATE case025_lib)
