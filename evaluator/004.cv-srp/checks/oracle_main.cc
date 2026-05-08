#include <iostream>
#include <string>

#include "io_json.h"
#include "legacy_monolith.h"
#include "types.h"

namespace {

struct Args {
  std::string input;
  std::string output;
};

bool ParseArgs(int argc, char** argv, Args* out) {
  for (int i = 1; i < argc; ++i) {
    std::string a = argv[i];
    if (a == "--input" && i + 1 < argc) {
      out->input = argv[++i];
    } else if (a == "--output" && i + 1 < argc) {
      out->output = argv[++i];
    }
  }
  if (out->input.empty() || out->output.empty()) {
    return false;
  }
  return true;
}

}  // namespace

int main(int argc, char** argv) {
  Args args;
  if (!ParseArgs(argc, argv, &args)) {
    std::cerr << nitr::case004::ToStderrString(
                     nitr::case004::ErrorCode::kInvalidSchema)
              << "\n";
    return nitr::case004::ToExitCode(nitr::case004::ErrorCode::kInvalidSchema);
  }
  // Parse
  nitr::case004::ParseOutput parsed =
      nitr::case004::ParsePairJsonFromFile(args.input);
  if (!parsed.input.has_value()) {
    std::cerr << nitr::case004::ToStderrString(parsed.err) << "\n";
    return nitr::case004::ToExitCode(parsed.err);
  }
  nitr::case004::ErrorCode code =
      nitr::case004::RunLegacyMonolith(args.input, args.output);

  if (code != nitr::case004::ErrorCode::kOk) {
    std::cerr << nitr::case004::ToStderrString(code) << "\n";
  }

  return nitr::case004::ToExitCode(code);
}
