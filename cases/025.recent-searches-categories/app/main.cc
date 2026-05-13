#include <iostream>
#include <string>
#include <utility>
#include <vector>

#include "recent_searches.h"
#include "reporter.h"
#include "search.h"

int main() {
    using namespace nitr::case025;

    RecentSearches recent;
    Search search(recent);

    const std::vector<std::pair<std::string, std::string>> search_strings = {
        {"book", "harry potter"},
        {"video", "cooking"},
        {"book", "lord of the rings"},
        {"image", "sunset"},
    };

    for (const std::pair<std::string, std::string>& search_string : search_strings) {
        std::cout << search.Item(search_string.first, search_string.second) << '\n';
    }

    Reporter reporter(recent);
    std::cout << reporter.Summary() << '\n';

    std::cout << "categories seen:";
    for (const std::string& category : recent.CategoriesSeen()) {
        std::cout << ' ' << category;
    }
    std::cout << '\n';

    for (const std::string& category : recent.CategoriesSeen()) {
        std::cout << category << " count: " << recent.CountByCategory(category) << '\n';
    }

    return 0;
}
