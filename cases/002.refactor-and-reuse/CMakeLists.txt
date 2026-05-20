cmake_minimum_required(VERSION 3.16)

# ---- SRP impl library (NO legacy) ----
add_library(mvg_lib
  src/geometry.cc
)

target_include_directories(mvg_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_include_directories(mvg_lib PUBLIC ${CMAKE_SOURCE_DIR}/third_party/eigen3)
target_link_libraries(mvg_lib PUBLIC nlohmann_json)

# ---- main binary (SRP path only) ----
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/app/main.cc)
  add_executable(run_mvp app/main.cc)
  target_link_libraries(run_mvp PRIVATE mvg_lib)
endif()
