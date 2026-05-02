#pragma once

#include "submission.h"

namespace nitr::case023 {

class Validator {
   public:
    bool validate(const Submission& s) const;
};

}  // namespace nitr::case023