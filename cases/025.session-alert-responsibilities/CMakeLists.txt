## Case 025: session alert responsibilities

cmake_minimum_required(VERSION 3.16)
project(case025_session_alert_responsibilities LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Library containing the session-monitor implementation.
add_library(case_025_lib
    src/monitor.cc
)

target_include_directories(case_025_lib
    PUBLIC
        src
)

# Tiny executable to exercise the monitor.  Not used by the evaluator; it only
# supports local debugging.
add_executable(nitr_025_session_alert_responsibilities_app
    app/main.cc
)

target_link_libraries(nitr_025_session_alert_responsibilities_app
    case_025_lib
)
