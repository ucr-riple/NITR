cmake_minimum_required(VERSION 3.16)
project(case025_recent_searches_categories LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(case025_lib
    src/recent_searches.cc
    src/reporter.cc
    src/search.cc
)
target_include_directories(case025_lib PUBLIC src)

add_executable(case025_app app/main.cc)
target_link_libraries(case025_app PRIVATE case025_lib)
