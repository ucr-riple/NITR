#pragma once

#include <fstream>
#include <string>
#include <vector>

#include "event.h"

namespace case015_test {

inline std::vector<nitr::case015::Event> SampleEvents() {
  return {
      {"web", "login ok", 8},
      {"mobile", "purchase confirmed", 12},
      {"unknown", "manual review", 3},
  };
}

inline std::vector<std::string> ReadExpectedLines(const std::string& path) {
  std::ifstream input(path);
  std::vector<std::string> lines;
  std::string line;
  while (std::getline(input, line)) {
    if (!line.empty()) {
      lines.push_back(line);
    }
  }
  return lines;
}

}  // namespace case015_test
