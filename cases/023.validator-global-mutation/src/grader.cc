#include "grader.h"

#include <algorithm>

namespace nitr::case023 {

int Grader::Grade(const Submission& s) const {
    const int length_score = static_cast<int>(std::min<std::size_t>(s.content.size(), 100));
    return length_score;
}

}  // namespace nitr::case023
