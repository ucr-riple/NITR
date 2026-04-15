cmake_minimum_required(VERSION 3.16)

add_subdirectory(
  ${CMAKE_SOURCE_DIR}/third_party/googletest
  ${CMAKE_BINARY_DIR}/_deps/googletest-build
  EXCLUDE_FROM_ALL
)

find_package(Python3 COMPONENTS Interpreter REQUIRED)
find_program(BASH_PROGRAM bash)

option(CASE015_ENABLE_VISIBLE_CHECKS "Run visible structural checks via CTest" ON)
option(CASE015_ENABLE_HIDDEN_EVALUATOR "Enable hidden tests and hidden checks" OFF)

function(nitr_case_source_dir out_var case_dir)
  set(${out_var} ${CMAKE_SOURCE_DIR}/cases/${case_dir} PARENT_SCOPE)
endfunction()

function(nitr_case_evaluator_dir out_var case_dir)
  set(${out_var} ${CMAKE_CURRENT_SOURCE_DIR}/${case_dir} PARENT_SCOPE)
endfunction()

function(nitr_add_gtest test_name case_target test_source)
  add_executable(${test_name} ${test_source})
  target_link_libraries(${test_name} PRIVATE ${case_target} gtest_main)
  add_test(NAME ${test_name} COMMAND ${test_name})
endfunction()

function(nitr_add_plain_test test_name case_target test_source)
  add_executable(${test_name} ${test_source})
  target_link_libraries(${test_name} PRIVATE ${case_target})
  add_test(NAME ${test_name} COMMAND ${test_name})
endfunction()

function(nitr_register_case_001)
  nitr_case_evaluator_dir(EVAL_DIR 001.add-no-callsite-spread)
  nitr_add_gtest(add_tests add_lib ${EVAL_DIR}/tests/test_add.cc)
endfunction()

function(nitr_register_case_002)
  nitr_case_source_dir(CASE_DIR 002.refactor-and-resue)
  nitr_case_evaluator_dir(EVAL_DIR 002.refactor-and-resue)
  nitr_add_gtest(geometry_tests mvg_lib ${EVAL_DIR}/tests/test_geometry.cc)
  add_test(
    NAME geometry_structure_check
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/check_geometry_structure.py ${CASE_DIR}
  )
endfunction()

function(nitr_register_case_003)
  nitr_case_source_dir(CASE_DIR 003.reuse-existing-code)
  nitr_case_evaluator_dir(EVAL_DIR 003.reuse-existing-code)
  add_executable(case003_functional_tests
    ${EVAL_DIR}/tests/test_cosine_similarity.cc
  )
  target_link_libraries(case003_functional_tests PRIVATE case003_lib)
  add_test(NAME case003_functional_tests COMMAND case003_functional_tests)

  add_executable(case003_reuse_check
    ${EVAL_DIR}/checks/check_reuse_existing_step.cc
  )
  add_test(NAME maintainbench_reuse_existing_step COMMAND case003_reuse_check)
  set_tests_properties(maintainbench_reuse_existing_step PROPERTIES WORKING_DIRECTORY ${CASE_DIR})
endfunction()

function(nitr_register_case_004)
  nitr_case_source_dir(CASE_DIR 004.cv-srp)
  nitr_case_evaluator_dir(EVAL_DIR 004.cv-srp)

  add_executable(cv_srp_oracle
    ${EVAL_DIR}/checks/oracle_main.cc
    ${CASE_DIR}/src/legacy_monolith.cc
  )
  target_include_directories(cv_srp_oracle PRIVATE ${CASE_DIR}/src)
  target_link_libraries(cv_srp_oracle PRIVATE nlohmann_json cv_srp_lib)

  add_executable(cv_srp_tests
    ${EVAL_DIR}/tests/test_io_json.cc
    ${EVAL_DIR}/tests/test_scoring.cc
    ${EVAL_DIR}/tests/test_policy.cc
    ${EVAL_DIR}/tests/test_pipeline.cc
  )
  target_link_libraries(cv_srp_tests PRIVATE cv_srp_lib gtest_main)
  add_test(NAME cv_srp_tests COMMAND cv_srp_tests)
endfunction()

function(nitr_register_case_005)
  nitr_case_evaluator_dir(EVAL_DIR 005.pricing-ocp)
  nitr_add_gtest(pricing_ocp_tests pricing_ocp_lib ${EVAL_DIR}/tests/test_pricing.cc)
endfunction()

function(nitr_register_case_006)
  nitr_case_evaluator_dir(EVAL_DIR 006.gs-isp)
  nitr_add_plain_test(public_smoke_test case006_lib ${EVAL_DIR}/tests/public_smoke_test.cc)
endfunction()

function(nitr_register_case_007)
  nitr_case_evaluator_dir(EVAL_DIR 007.ml-lsp-multistep)
  nitr_add_plain_test(case007_public_tests case007_core ${EVAL_DIR}/tests/test_public.cc)
  nitr_add_plain_test(case007_hidden_tests case007_core ${EVAL_DIR}/tests/test_hidden.cc)
  add_test(
    NAME case007_constraint_checks
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/verify_constraints.py
  )
endfunction()

function(nitr_register_case_008)
  nitr_case_evaluator_dir(EVAL_DIR 008.map-dip)
  nitr_add_plain_test(test_basic case008_lib ${EVAL_DIR}/tests/test_basic.cc)
  add_test(NAME case008_basic COMMAND test_basic)
endfunction()

function(nitr_register_case_009)
  nitr_case_evaluator_dir(EVAL_DIR 009.session-expiry-testability)
  nitr_add_plain_test(session_manager_test case009_lib ${EVAL_DIR}/tests/session_manager_test.cc)
  add_test(
    NAME maintainability_check_case009
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/maintainability_check.py
  )
endfunction()

function(nitr_register_case_010)
  nitr_case_evaluator_dir(EVAL_DIR 010.logging-side-effects)
  nitr_add_plain_test(loan_review_test case010_lib ${EVAL_DIR}/tests/loan_review_test.cc)
  add_test(
    NAME maintainability_check_case010
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/maintainability_check.py
  )
endfunction()

function(nitr_register_case_011)
  nitr_case_evaluator_dir(EVAL_DIR 011.config-sprawl)
  nitr_add_plain_test(case011_tests case011_lib ${EVAL_DIR}/tests/test_config_sprawl.cc)
endfunction()

function(nitr_register_case_012)
  nitr_case_evaluator_dir(EVAL_DIR 012.cache-lifecycle)
  nitr_add_plain_test(report_cache_test case012_lib ${EVAL_DIR}/tests/report_cache_test.cc)
  add_test(
    NAME maintainability_check_case012
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/maintainability_check.py
  )
endfunction()

function(nitr_register_case_013)
  nitr_case_evaluator_dir(EVAL_DIR 013.stable-public-api)
  nitr_add_plain_test(test_catalog case013_lib ${EVAL_DIR}/tests/test_catalog.cc)
endfunction()

function(nitr_register_case_014)
  nitr_case_evaluator_dir(EVAL_DIR 014.report-export-ocp)
  nitr_add_plain_test(test_report_export case014_lib ${EVAL_DIR}/tests/test_report_export.cc)
endfunction()

function(nitr_add_case015_test test_name test_source)
  add_executable(${test_name} ${test_source})
  target_include_directories(${test_name} PRIVATE
    ${CMAKE_SOURCE_DIR}/cases/015.pipeline-provider-decoupling/src
    ${CMAKE_CURRENT_SOURCE_DIR}/015.pipeline-provider-decoupling/tests
  )
  target_link_libraries(${test_name} PRIVATE case015_core)
  add_test(NAME ${test_name} COMMAND ${test_name})
  set_tests_properties(${test_name} PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
endfunction()

function(nitr_add_case015_python_test test_name script_path)
  add_test(NAME ${test_name}
    COMMAND ${Python3_EXECUTABLE} ${script_path} ${ARGN}
  )
  set_tests_properties(${test_name} PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
endfunction()

function(nitr_register_case_015)
  nitr_case_evaluator_dir(EVAL_DIR 015.pipeline-provider-decoupling)

  nitr_add_case015_test(test_pipeline_behavior ${EVAL_DIR}/tests/test_pipeline_behavior.cc)
  nitr_add_case015_test(test_policy_enrichment_static ${EVAL_DIR}/tests/test_policy_enrichment_static.cc)
  nitr_add_case015_test(test_policy_enrichment_file ${EVAL_DIR}/tests/test_policy_enrichment_file.cc)
  nitr_add_case015_test(test_provider_switching ${EVAL_DIR}/tests/test_provider_switching.cc)

  if(CASE015_ENABLE_VISIBLE_CHECKS)
    nitr_add_case015_python_test(
      check_no_concrete_provider_in_core
      ${EVAL_DIR}/checks/check_no_concrete_provider_in_core.py
    )
    nitr_add_case015_python_test(
      check_no_provider_creation_from_core
      ${EVAL_DIR}/checks/check_no_provider_creation_from_core.py
    )
    nitr_add_case015_python_test(
      check_single_wiring_boundary
      ${EVAL_DIR}/checks/check_single_wiring_boundary.py
    )
  endif()

  if(CASE015_ENABLE_HIDDEN_EVALUATOR)
    nitr_add_case015_test(
      hidden_test_policy_enrichment_static_exact
      ${EVAL_DIR}/tests/hidden_test_policy_enrichment_static_exact.cc
    )
    nitr_add_case015_test(
      hidden_test_policy_enrichment_file_exact
      ${EVAL_DIR}/tests/hidden_test_policy_enrichment_file_exact.cc
    )
    nitr_add_case015_test(
      hidden_test_policy_fallback_and_partner
      ${EVAL_DIR}/tests/hidden_test_policy_fallback_and_partner.cc
    )

    nitr_add_case015_python_test(
      hidden_cli_static_output
      ${EVAL_DIR}/tests/check_cli_output.py
      $<TARGET_FILE:case015_app>
      ${CMAKE_SOURCE_DIR}
      evaluator/015.pipeline-provider-decoupling/data/expected_output_static.txt
      --enable-policy-enrichment
      --mode=static
    )
    nitr_add_case015_python_test(
      hidden_cli_file_output
      ${EVAL_DIR}/tests/check_cli_output.py
      $<TARGET_FILE:case015_app>
      ${CMAKE_SOURCE_DIR}
      evaluator/015.pipeline-provider-decoupling/data/expected_output_file.txt
      --enable-policy-enrichment
      --mode=file
      --policy-file=evaluator/015.pipeline-provider-decoupling/data/policies.json
    )
    nitr_add_case015_python_test(
      hidden_check_pipeline_runner_contract_surface
      ${EVAL_DIR}/checks/hidden_check_pipeline_runner_contract_surface.py
    )
    nitr_add_case015_python_test(
      hidden_check_boundary_wiring_presence
      ${EVAL_DIR}/checks/hidden_check_boundary_wiring_presence.py
    )
  endif()
endfunction()

function(nitr_register_case_016)
  nitr_case_source_dir(CASE_DIR 016.device-segment-planner)
  nitr_case_evaluator_dir(EVAL_DIR 016.device-segment-planner)

  function(add_case016_test test_name source_file)
    add_executable(${test_name} ${source_file})
    target_include_directories(${test_name} PRIVATE ${EVAL_DIR}/tests ${CASE_DIR}/src)
    target_link_libraries(${test_name} PRIVATE case016_lib)
    add_test(NAME ${test_name} COMMAND ${test_name})
    set_tests_properties(${test_name} PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
  endfunction()

  add_case016_test(config_loader_smoke_test ${EVAL_DIR}/tests/config_loader_smoke_test.cc)
  add_case016_test(runner_smoke_test ${EVAL_DIR}/tests/runner_smoke_test.cc)
  add_case016_test(execution_plan_legacy_test ${EVAL_DIR}/tests/execution_plan_legacy_test.cc)
  add_case016_test(execution_plan_updated_test ${EVAL_DIR}/tests/execution_plan_updated_test.cc)
  add_case016_test(execution_plan_unseen_test ${EVAL_DIR}/tests/execution_plan_unseen_test.cc)
  add_case016_test(runner_respects_segmentation_test ${EVAL_DIR}/tests/runner_respects_segmentation_test.cc)

  add_test(
    NAME require_planner_usage_check
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/require_planner_usage.py
  )
  set_tests_properties(require_planner_usage_check PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

  add_test(
    NAME no_step_index_special_case_check
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/no_step_index_special_case.py
  )
  set_tests_properties(no_step_index_special_case_check PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
endfunction()

function(nitr_register_case_017)
  nitr_case_evaluator_dir(EVAL_DIR 017.active-snapshot-lifecycle)
  nitr_add_plain_test(case017_lifecycle_tests case017_lib ${EVAL_DIR}/tests/test_lifecycle.cc)
  add_test(
    NAME case017_structure_checks
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/check_structure.py
  )
  set_tests_properties(case017_structure_checks PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
endfunction()

function(nitr_register_case_018)
  nitr_case_evaluator_dir(EVAL_DIR 018.seeded-selection-testability)
  nitr_add_plain_test(case018_evaluator_tests case018_core ${EVAL_DIR}/tests/case018_evaluator_test.cc)
  add_test(
    NAME case018_structural_checks
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/run_evaluator.py
  )
  set_tests_properties(case018_structural_checks PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
endfunction()

function(nitr_register_case_019)
  nitr_case_source_dir(CASE_DIR 019.ranking-explainability-boundary)
  nitr_case_evaluator_dir(EVAL_DIR 019.ranking-explainability-boundary)

  add_executable(case019_baseline_test ${EVAL_DIR}/tests/baseline_test.cc)
  target_link_libraries(case019_baseline_test PRIVATE case019_ranking)
  add_test(NAME case019_baseline_test COMMAND case019_baseline_test)

  add_executable(case019_feature_reason_test ${EVAL_DIR}/tests/feature_reason_test.cc)
  target_link_libraries(case019_feature_reason_test PRIVATE case019_ranking)
  target_include_directories(case019_feature_reason_test PRIVATE ${EVAL_DIR}/tests)
  add_test(NAME case019_feature_reason_test COMMAND case019_feature_reason_test)

  add_executable(case019_inspect_compare_test ${EVAL_DIR}/tests/inspect_compare_test.cc)
  target_link_libraries(case019_inspect_compare_test PRIVATE case019_ranking)
  target_include_directories(case019_inspect_compare_test PRIVATE ${EVAL_DIR}/tests)
  add_test(NAME case019_inspect_compare_test COMMAND case019_inspect_compare_test)

  add_test(
    NAME case019_structural_check
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/structural_check.py ${CASE_DIR}
  )
endfunction()

function(nitr_register_case_020)
  nitr_case_evaluator_dir(EVAL_DIR 020.handover-packet-ownership-boundary)
  add_test(
    NAME case020_evaluator
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/run_evaluator.py
  )
  set_tests_properties(case020_evaluator PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
endfunction()

function(nitr_register_case_021)
  nitr_case_source_dir(CASE_DIR 021.inline-filter-entrypoint-reuse)
  nitr_case_evaluator_dir(EVAL_DIR 021.inline-filter-entrypoint-reuse)

  add_executable(case021_evaluator_tests ${EVAL_DIR}/tests/filter_evaluator_tests.cc)
  target_include_directories(case021_evaluator_tests PRIVATE ${CASE_DIR}/src)
  target_compile_definitions(case021_evaluator_tests PRIVATE EVALUATOR_DATA_DIR="${EVAL_DIR}/data")
  target_link_libraries(case021_evaluator_tests PRIVATE case021_lib)

  add_test(NAME case021_functional_tests COMMAND case021_evaluator_tests)
endfunction()

function(nitr_register_case_022)
  nitr_case_source_dir(CASE_DIR 022.thermostat-sensor-decoupling)
  nitr_case_evaluator_dir(EVAL_DIR 022.thermostat-sensor-decoupling)

  nitr_add_gtest(
    case022_thermostat_tests
    case022_lib
    ${EVAL_DIR}/tests/test_thermostat.cc
  )
  
  add_test(
    NAME case022_functional_tests
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/tests/test_functional.py $<TARGET_FILE:case022_app>
  )
  
  add_test(
    NAME case022_dependency_check
    COMMAND ${Python3_EXECUTABLE} ${EVAL_DIR}/checks/check_dependency.py ${CASE_DIR}
  )
endfunction()

function(nitr_add_evaluator case_dir)
  if(case_dir STREQUAL "001.add-no-callsite-spread")
    nitr_register_case_001()
  elseif(case_dir STREQUAL "002.refactor-and-resue")
    nitr_register_case_002()
  elseif(case_dir STREQUAL "003.reuse-existing-code")
    nitr_register_case_003()
  elseif(case_dir STREQUAL "004.cv-srp")
    nitr_register_case_004()
  elseif(case_dir STREQUAL "005.pricing-ocp")
    nitr_register_case_005()
  elseif(case_dir STREQUAL "006.gs-isp")
    nitr_register_case_006()
  elseif(case_dir STREQUAL "007.ml-lsp-multistep")
    nitr_register_case_007()
  elseif(case_dir STREQUAL "008.map-dip")
    nitr_register_case_008()
  elseif(case_dir STREQUAL "009.session-expiry-testability")
    nitr_register_case_009()
  elseif(case_dir STREQUAL "010.logging-side-effects")
    nitr_register_case_010()
  elseif(case_dir STREQUAL "011.config-sprawl")
    nitr_register_case_011()
  elseif(case_dir STREQUAL "012.cache-lifecycle")
    nitr_register_case_012()
  elseif(case_dir STREQUAL "013.stable-public-api")
    nitr_register_case_013()
  elseif(case_dir STREQUAL "014.report-export-ocp")
    nitr_register_case_014()
  elseif(case_dir STREQUAL "015.pipeline-provider-decoupling")
    nitr_register_case_015()
  elseif(case_dir STREQUAL "016.device-segment-planner")
    nitr_register_case_016()
  elseif(case_dir STREQUAL "017.active-snapshot-lifecycle")
    nitr_register_case_017()
  elseif(case_dir STREQUAL "018.seeded-selection-testability")
    nitr_register_case_018()
  elseif(case_dir STREQUAL "019.ranking-explainability-boundary")
    nitr_register_case_019()
  elseif(case_dir STREQUAL "020.handover-packet-ownership-boundary")
    nitr_register_case_020()
  elseif(case_dir STREQUAL "021.inline-filter-entrypoint-reuse")
    nitr_register_case_021()
  elseif(case_dir STREQUAL "022.thermostat-sensor-decoupling")
    nitr_register_case_022()
  endif()
endfunction()

if(NITR_BUILD_ALL_CASES)
  nitr_add_evaluator(001.add-no-callsite-spread)
  nitr_add_evaluator(002.refactor-and-resue)
  nitr_add_evaluator(003.reuse-existing-code)
  nitr_add_evaluator(004.cv-srp)
  nitr_add_evaluator(005.pricing-ocp)
  nitr_add_evaluator(006.gs-isp)
  nitr_add_evaluator(007.ml-lsp-multistep)
  nitr_add_evaluator(008.map-dip)
  nitr_add_evaluator(009.session-expiry-testability)
  nitr_add_evaluator(010.logging-side-effects)
  nitr_add_evaluator(011.config-sprawl)
  nitr_add_evaluator(012.cache-lifecycle)
  nitr_add_evaluator(013.stable-public-api)
  nitr_add_evaluator(014.report-export-ocp)
  nitr_add_evaluator(015.pipeline-provider-decoupling)
  nitr_add_evaluator(016.device-segment-planner)
  nitr_add_evaluator(017.active-snapshot-lifecycle)
  nitr_add_evaluator(018.seeded-selection-testability)
  nitr_add_evaluator(019.ranking-explainability-boundary)
  nitr_add_evaluator(020.handover-packet-ownership-boundary)
  nitr_add_evaluator(021.inline-filter-entrypoint-reuse)
  nitr_add_evaluator(022.thermostat-sensor-decoupling)
elseif(NOT NITR_CASE STREQUAL "")
  nitr_add_evaluator(${NITR_CASE})
endif()
