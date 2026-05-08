#pragma once

#include <string>

namespace nitr::case023 {

struct Submission {
  std::string student_id;
  std::string content;
  bool is_late = false;
};

}  // namespace nitr::case023
