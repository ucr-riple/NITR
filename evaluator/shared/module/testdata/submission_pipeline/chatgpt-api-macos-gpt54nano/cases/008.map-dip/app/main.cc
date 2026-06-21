#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>
#include <sstream>
#include <string>

#include "map_snapshot.h"

using nitr::case008::MapSnapshotService;

static std::string ReadAllStdin() {
  std::ostringstream oss;
  oss << std::cin.rdbuf();
  return oss.str();
}

int main(int argc, char** argv) {
  if (argc != 2) {
    std::cerr << "Usage: map_snapshot <config.json>\n";
    return 2;
  }

  std::ifstream ifs(argv[1]);
  if (!ifs) {
    std::cerr << "Failed to open config\n";
    return 2;
  }

  nlohmann::json cfg;
  try {
    ifs >> cfg;
  } catch (const std::exception& e) {
    std::cerr << "Failed to parse JSON: " << e.what() << "\n";
    return 2;
  }

  const std::string payload = ReadAllStdin();

  try {
    MapSnapshotService svc;
    std::cout << svc.BuildSnapshot(cfg, payload);
  } catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << "\n";
    return 1;
  }

  return 0;
}
