#pragma once

#include <string>
#include <vector>

namespace nitr::case024 {

class RecentSearches {
   private:
    std::vector<std::string> searches_;
    
   public:
    void Record(const std::string& term);
    void Clear();

    bool Contains(const std::string& term) const;
    int CountByCategory(const std::string& category) const;

    const std::vector<std::string>& Terms() const;
};

}  // namespace nitr::case024
