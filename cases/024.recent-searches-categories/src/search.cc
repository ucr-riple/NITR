#include "search.h"

namespace nitr::case024 {

Search::Search(RecentSearches& recent) : recent_(recent) {}

std::string Search::Item(const std::string& category, const std::string& search_word) {
    const std::string entry = category + ":" + search_word;
    recent_.Record(entry);
    return "results for: " + entry;
}

}  // namespace nitr::case024
