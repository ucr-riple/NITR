#include <gtest/gtest.h>

#include <string>

#include "recent_searches.h"
#include "reporter.h"
#include "search.h"


TEST(CountByCategoryTest, ReturnsZeroWhenEmpty) {
    nitr::case025::RecentSearches recent;
    EXPECT_EQ(recent.CountByCategory("book"), 0);
}

TEST(CountByCategoryTest, ReturnsZeroWhenNoEntriesInCategory) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");
    recent.Record("book:the dark tower");

    EXPECT_EQ(recent.CountByCategory("video"), 0);
}

TEST(CountByCategoryTest, CountSingleEntry) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");

    EXPECT_EQ(recent.CountByCategory("book"), 1);
}

TEST(CountByCategoryTest, CountsMultipleEntriesInSameCategory) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");
    recent.Record("book:the dark tower");
    recent.Record("book:lord of the rings");

    EXPECT_EQ(recent.CountByCategory("book"), 3);
}

TEST(CountByCategoryTest, CountsAcrossMultipleCategories) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");
    recent.Record("video:cooking");
    recent.Record("book:the dark tower");
    recent.Record("image:sunglasses");
    recent.Record("video:free music");

    EXPECT_EQ(recent.CountByCategory("book"), 2);
    EXPECT_EQ(recent.CountByCategory("video"), 2);
    EXPECT_EQ(recent.CountByCategory("image"), 1);
}

TEST(CountByCategoryTest, NoCountWhenMissingSeparator) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");
    recent.Record("scifi");
    recent.Record("none");

    EXPECT_EQ(recent.CountByCategory("book"), 1);
    EXPECT_EQ(recent.CountByCategory("scifi"), 0);
}

TEST(CountByCategoryTest, RequireExactPrefixMatch) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");

    EXPECT_EQ(recent.CountByCategory("oo"), 0);
    EXPECT_EQ(recent.CountByCategory("books"), 0);
    EXPECT_EQ(recent.CountByCategory("boo"), 0);
}

TEST(CategoriesSeenTest, EmptyWhenNoSearches) {
    nitr::case025::RecentSearches recent;
    EXPECT_TRUE(recent.CategoriesSeen().empty());
}

TEST(CategoriesSeenTest, SingleCategorySingleEntry) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");

    const std::vector<std::string> expected = {"book"};
    EXPECT_EQ(recent.CategoriesSeen(), expected);
}

TEST(CategoriesSeenTest, DuplicatesRepeatedCategory) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");
    recent.Record("book:the dark tower");
    recent.Record("book:lord of the rings");

    const std::vector<std::string> expected = {"book"};
    EXPECT_EQ(recent.CategoriesSeen(), expected);
}

TEST(CategoriesSeenTest, CorrectAppearanceOrder) {
    nitr::case025::RecentSearches recent;
    recent.Record("video:cooking");
    recent.Record("book:harry potter");
    recent.Record("video:free music");
    recent.Record("image:oceans");
    recent.Record("book:the dark tower");

    const std::vector<std::string> expected = {"video", "book", "image"};
    EXPECT_EQ(recent.CategoriesSeen(), expected);
}

TEST(CategoriesSeenTest, IgnoresEntriesWithOutSeparator) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");
    recent.Record("scifi");
    recent.Record("video:cooking");
    recent.Record("none");

    const std::vector<std::string> expected = {"book", "video"};
    EXPECT_EQ(recent.CategoriesSeen(), expected);
}

TEST(CategoriesSeenTest, EmptyCategoryPrefixIsValid) {
    nitr::case025::RecentSearches recent;
    recent.Record(":mystery");
    recent.Record("book:harry potter");

    const std::vector<std::string> expected = {"", "book"};
    EXPECT_EQ(recent.CategoriesSeen(), expected);
}

TEST(CategoryConsistencyTest, CountMatchesCategoriesSeen) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");
    recent.Record("video:cooking");
    recent.Record("book:the dark tower");

    int total = 0;
    for (const std::string& category : recent.CategoriesSeen()) {
        total += recent.CountByCategory(category);
    }
    EXPECT_EQ(total, 3);
}

TEST(ContainsRegressionTest, ReturnsTrueForRecordedEntry) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:harry potter");

    EXPECT_TRUE(recent.Contains("book:harry potter"));
    EXPECT_FALSE(recent.Contains("book:titanic"));
}

TEST(SearchFlowTest, RecordsCategorizedEntries) {
    nitr::case025::RecentSearches recent;
    nitr::case025::Search search(recent);

    search.Item("book", "harry potter");
    search.Item("video", "the new yorker");

    EXPECT_EQ(recent.CountByCategory("book"), 1);
    EXPECT_EQ(recent.CountByCategory("video"), 1);
    EXPECT_TRUE(recent.Contains("book:harry potter"));
}

TEST(ReporterRegressionTest, PerCategoryBreakdown) {
    nitr::case025::RecentSearches recent;
    recent.Record("book:the goldfinch");
    recent.Record("video:secret history");

    nitr::case025::Reporter reporter(recent);
    EXPECT_EQ(reporter.Summary(),
              "Recent [book=1, video=1]: book:the goldfinch, video:secret history");
}

TEST(ReporterRegressionTest, EmptyBufferSummary) {
    nitr::case025::RecentSearches recent;
    nitr::case025::Reporter reporter(recent);

    EXPECT_EQ(reporter.Summary(), "Recent []: ");
}
