include(${CMAKE_CURRENT_LIST_DIR}/../PythonTestArgs.cmake)

set(cases_root /repo/cases)
set(case_path ${cases_root}/example-case)

nitr_check_python_test_args(error_message ${cases_root} --case_root ${case_path})
if(error_message)
  message(FATAL_ERROR "named case path was rejected: ${error_message}")
endif()

nitr_check_python_test_args(error_message ${cases_root} --case_dir ${case_path})
if(error_message)
  message(FATAL_ERROR "alternate named case path was rejected: ${error_message}")
endif()

nitr_check_python_test_args(error_message ${cases_root} ${case_path})
if(NOT error_message)
  message(FATAL_ERROR "positional case path was accepted")
endif()
