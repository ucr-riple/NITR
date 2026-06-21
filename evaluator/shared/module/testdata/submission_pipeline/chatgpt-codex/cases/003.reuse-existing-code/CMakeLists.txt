cmake_minimum_required(VERSION 3.16)
project(case003_reuse_existing_code LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(MAINTAINBENCH_WARNINGS_AS_ERRORS "Treat warnings as errors" ON)
if (MAINTAINBENCH_WARNINGS_AS_ERRORS)
  if (MSVC)
    add_compile_options(/W4 /WX)
  else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
  endif()
endif()

add_library(case003_lib
  src/dot_product.cc
  src/l2_norm.cc
  src/cosine_similarity.cc
)
target_include_directories(case003_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)

add_executable(case003_app
  app/main.cc
)
target_link_libraries(case003_app PRIVATE case003_lib)
