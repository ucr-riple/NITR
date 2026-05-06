#pragma once

#include <string>

#include "recent_searches.h"

namespace nitr::case024 {

class Search {
   private:
    RecentSearches& recent_;
    
   public:
    Search(RecentSearches& recent);

    std::string Item(const std::string& category, const std::string& search_word);
};

}  // namespace nitr::case024
