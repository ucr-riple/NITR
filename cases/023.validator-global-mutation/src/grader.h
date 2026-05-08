#pragma once
#include "submission.h"

namespace nitr::case023 {

class Grader {
 public:
  int Grade(const Submission& s) const;
};

}  // namespace nitr::case023