#include <cassert>
#include <fstream>
#include <iostream>
#include <regex>
#include <string>

// This check enforces "reuse existing step" by requiring CosineSimilarity
// to call nitr::case003::DotProduct and nitr::case003::L2Norm rather than
// re-implementing those computations.

static std::string ReadAll(const std::string& path) {
  std::ifstream ifs(path);
  if (!ifs) {
    return "";
  }
  return std::string((std::istreambuf_iterator<char>(ifs)),
                     std::istreambuf_iterator<char>());
}

static bool RegexSearch(const std::string& s, const std::regex& re) {
  return std::regex_search(s, re);
}

int main() {
  const std::string path = "src/cosine_similarity.cc";
  const std::string code = ReadAll(path);
  if (code.empty()) {
    std::cerr << "Failed to read " << path << std::endl;
    return 1;
  }

  // Must include the utilities and call them.
  const std::regex re_inc_dot(R"(#include\s+"dot_product\.h")");
  const std::regex re_inc_l2(R"(#include\s+"l2_norm\.h")");
  const std::regex re_call_dot(R"((?:nitr::case003::)?DotProduct\s*\()");
  const std::regex re_call_l2(R"((?:nitr::case003::)?L2Norm\s*\()");
  assert(RegexSearch(code, re_inc_dot));
  assert(RegexSearch(code, re_inc_l2));
  assert(RegexSearch(code, re_call_dot));
  assert(RegexSearch(code, re_call_l2));

  // Heuristic anti-duplication: discourage direct sqrt or manual dot/norm loops.
  // (This is deliberately narrow to keep false positives low.)
  const std::regex re_sqrt(R"(\bsqrt\s*\()");
  const std::regex re_sum_sq(R"(sum_sq\s*\+=)");
  const std::regex re_mul_acc(R"(sum\s*\+=\s*[^;]*\*[^;]*;)");
  if (RegexSearch(code, re_sqrt) || RegexSearch(code, re_sum_sq) ||
      RegexSearch(code, re_mul_acc)) {
    std::cerr << "Structural check failed: detected likely re-implementation "
                 "of math utilities in "
              << path << std::endl;
    return 1;
  }

  std::cout << "Structural reuse check passed." << std::endl;
  return 0;
}
