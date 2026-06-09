cmake_minimum_required(VERSION 3.16)
project(NITR LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(CTest)

if(BUILD_TESTING)
  add_test(
    NAME nitr_format_check
    COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/tools/check_format.sh
  )
  add_test(
    NAME nitr_python_format_check
    COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/tools/check_python_format.sh
  )
endif()

add_subdirectory(cases)

option(NITR_BUILD_EVALUATOR "Build evaluator targets and register evaluator tests" OFF)
if(NITR_BUILD_EVALUATOR)
  add_subdirectory(evaluator)
endif()
