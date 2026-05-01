cmake_minimum_required(VERSION 3.16)
project(case023_validator_global_mutation LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(case023_lib
    src/grader.cc
    src/reporter.cc
    src/stats.cc
)
target_include_directories(case023_lib PUBLIC src)

add_executable(case023_app app/main.cc)
target_link_libraries(case023_app PRIVATE case023_lib)
