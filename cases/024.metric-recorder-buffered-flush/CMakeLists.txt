cmake_minimum_required(VERSION 3.16)
project(case024_metric_recorder_buffered_flush LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(case024_lib
    src/console_metric_recorder.cc
    src/metric_collector.cc)

target_include_directories(case024_lib PUBLIC src)
target_compile_options(case024_lib PRIVATE -Wall -Wextra -Wpedantic)

add_executable(case024_app app/main.cc)
target_link_libraries(case024_app PRIVATE case024_lib)
