cmake_minimum_required(VERSION 3.16)
project(NITR LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(CTest)

if(BUILD_TESTING)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  add_test(
    NAME nitr_format_check
    COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/tools/check_format.sh
  )
  add_test(
    NAME nitr_python_format_check
    COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/tools/check_python_format.sh
  )
  add_test(
    NAME nitr_python_test_arg_consistency_test
    COMMAND ${CMAKE_COMMAND} -P
            ${CMAKE_CURRENT_SOURCE_DIR}/evaluator/cmake/tests/test_python_test_args.cmake
  )
  add_test(
    NAME nitr_all_python_test_registrations_consistency_test
    COMMAND
      ${CMAKE_COMMAND}
      -S ${CMAKE_CURRENT_SOURCE_DIR}
      -B ${CMAKE_CURRENT_BINARY_DIR}/all-python-test-registrations
      -DNITR_BUILD_ALL_CASES=ON
      -DNITR_BUILD_EVALUATOR=ON
  )
  add_test(
    NAME nitr_opencode_backend_tests
    COMMAND ${Python3_EXECUTABLE} -m unittest discover
            -s ${CMAKE_CURRENT_SOURCE_DIR}/submit/tests
            -p test_opencode_backend.py
  )
  add_test(
    NAME nitr_backend_registry_tests
    COMMAND ${Python3_EXECUTABLE} -m unittest discover
            -s ${CMAKE_CURRENT_SOURCE_DIR}/submit/tests
            -p test_backend_registry.py
  )
endif()

add_subdirectory(cases)

option(NITR_BUILD_EVALUATOR "Build evaluator targets and register evaluator tests" OFF)
if(NITR_BUILD_EVALUATOR)
  add_subdirectory(evaluator)
endif()
