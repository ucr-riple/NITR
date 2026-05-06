#include <gtest/gtest.h>

#include <string>

#include "recent_searches.h"
#include "reporter.h"
#include "search.h"


TEST(CountByCategoryTest, ReturnsZeroWhenEmpty) {
    nitr::case024::RecentSearches recent;
    EXPECT_EQ(recent.CountByCategory("book"), 0);
}

TEST(CountByCategoryTest, ReturnsZeroWhenNoEntriesInCategory) {
    nitr::case024::RecentSearches recent;
    recent.Record("book:harry potter");
    recent.Record("book:the dark tower");

    EXPECT_EQ(recent.CountByCategory("video"), 0);
}

TEST(CountByCategoryTest, CountSingleEntry) {
    nitr::case024::RecentSearches recent;
    recent.Record("book:harry potter");

    EXPECT_EQ(recent.CountByCategory("book"), 1);
}

TEST(CountByCategoryTest, CountsMultipleEntriesInSameCategory) {
    nitr::case024::RecentSearches recent;
    recent.Record("book:harry potter");
    recent.Record("book:the dark tower");
    recent.Record("book:lord of the rings");

    EXPECT_EQ(recent.CountByCategory("book"), 3);
}

TEST(CountByCategoryTest, CountsAcrossMultipleCategories) {
    nitr::case024::RecentSearches recent;
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
    nitr::case024::RecentSearches recent;
    recent.Record("book:harry potter");
    recent.Record("scifi");
    recent.Record("none");

    EXPECT_EQ(recent.CountByCategory("book"), 1);
    EXPECT_EQ(recent.CountByCategory("scifi"), 0);
}

TEST(CountByCategoryTest, RequireExactPrefixMatch) {
    nitr::case024::RecentSearches recent;
    recent.Record("book:harry potter");

    EXPECT_EQ(recent.CountByCategory("oo"), 0);
    EXPECT_EQ(recent.CountByCategory("books"), 0);
    EXPECT_EQ(recent.CountByCategory("boo"), 0);
}

TEST(ContainsRegressionTest, ReturnsTrueForRecordedEntry) {
    nitr::case024::RecentSearches recent;
    recent.Record("book:harry potter");

    EXPECT_TRUE(recent.Contains("book:harry potter"));
    EXPECT_FALSE(recent.Contains("book:titanic"));
}

TEST(SearchFlowTest, RecordsCategorizedEntries) {
    nitr::case024::RecentSearches recent;
    nitr::case024::Search search(recent);

    search.Item("book", "harry potter");
    search.Item("video", "the new yorker");

    EXPECT_EQ(recent.CountByCategory("book"), 1);
    EXPECT_EQ(recent.CountByCategory("video"), 1);
    EXPECT_TRUE(recent.Contains("book:harry potter"));
}

TEST(ReporterRegressionTest, AccuratelyReportsRecentSearches) {
    nitr::case024::RecentSearches recent;
    recent.Record("book:the goldfinch");
    recent.Record("video:secret history");

    nitr::case024::Reporter reporter(recent);
    EXPECT_EQ(reporter.Summary(), "Recent: book:the goldfinch, video:secret history");
}
