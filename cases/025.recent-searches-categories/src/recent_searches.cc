#include "recent_searches.h"

#include <algorithm>

namespace nitr::case025 {

const int MAX_SEARCHES = 5;

void RecentSearches::Record(const std::string& term) {
    searches_.push_back(term);
    if (static_cast<int>(searches_.size()) > MAX_SEARCHES) {
        searches_.erase(searches_.begin());
    }
}

void RecentSearches::Clear() {
    searches_.clear();
}

bool RecentSearches::Contains(const std::string& term) const {
    bool found = (std::find(searches_.begin(), searches_.end(), term) != searches_.end());
    return found;
}

int RecentSearches::CountByCategory(const std::string& category) const {
    return 0;
}

std::vector<std::string> RecentSearches::CategoriesSeen() const {
    return {};
}

const std::vector<std::string>& RecentSearches::Terms() const {
    return searches_;
}

}  // namespace nitr::case025
