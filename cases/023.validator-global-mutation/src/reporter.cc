#include "reporter.h"

#include <string>

#include "stats.h"

namespace nitr::case023 {

std::string Reporter::Summary() const {
  return "Processed " + std::to_string(total_processed) + " submissions";
}

}  // namespace nitr::case023
