function(nitr_check_python_test_args out_var cases_root)
  set(previous_argument_is_option FALSE)

  foreach(argument IN LISTS ARGN)
    string(FIND "${argument}" "${cases_root}/" cases_root_prefix)
    if(cases_root_prefix EQUAL 0 AND NOT previous_argument_is_option)
      set(
        ${out_var}
        "case path '${argument}' must be passed after a named option"
        PARENT_SCOPE
      )
      return()
    endif()

    if(argument MATCHES "^--")
      set(previous_argument_is_option TRUE)
    else()
      set(previous_argument_is_option FALSE)
    endif()
  endforeach()

  set(${out_var} "" PARENT_SCOPE)
endfunction()
