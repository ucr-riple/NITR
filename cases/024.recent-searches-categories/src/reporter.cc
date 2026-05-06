#include "reporter.h"

#include <string>

namespace nitr::case024 {

Reporter::Reporter(const RecentSearches& recent) : recent_(recent) {}

std::string Reporter::Summary() const {
    std::string output = " ";
    const std::vector<std::string>& terms = recent_.Terms();
    for (int i = 0; i < terms.size(); ++i) {
        if (i > 0) {
            output += ", ";
        }
        output += terms[i];
    }

    return "Recent: " + output;
}

}  // namespace nitr::case024
