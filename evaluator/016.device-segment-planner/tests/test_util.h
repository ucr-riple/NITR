#pragma once

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

#define ASSERT_TRUE(condition)                                                \
  do {                                                                        \
    if (!(condition)) {                                                       \
      std::ostringstream failure_stream;                                      \
      failure_stream << "Assertion failed: " #condition << " at " << __FILE__ \
                     << ":" << __LINE__;                                      \
      throw std::runtime_error(failure_stream.str());                         \
    }                                                                         \
  } while (false)

#define ASSERT_EQ(expected, actual)                                          \
  do {                                                                       \
    const auto expected_value = (expected);                                  \
    const auto actual_value = (actual);                                      \
    if (!(expected_value == actual_value)) {                                 \
      std::ostringstream failure_stream;                                     \
      failure_stream << "Assertion failed: expected '" << expected_value     \
                     << "' but got '" << actual_value << "' at " << __FILE__ \
                     << ":" << __LINE__;                                     \
      throw std::runtime_error(failure_stream.str());                        \
    }                                                                        \
  } while (false)

inline int RunTest(const std::string& test_name, void (*test_body)()) {
  try {
    test_body();
    std::cout << "[PASS] " << test_name << "\n";
    return EXIT_SUCCESS;
  } catch (const std::exception& error) {
    std::cerr << "[FAIL] " << test_name << ": " << error.what() << "\n";
    return EXIT_FAILURE;
  }
}
