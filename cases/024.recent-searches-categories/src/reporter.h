#pragma once

#include <string>

#include "recent_searches.h"

namespace nitr::case024 {

class Reporter {
   private:
    const RecentSearches& recent_;
    
   public:
    Reporter(const RecentSearches& recent);

    std::string Summary() const;
};

}  // namespace nitr::case024
