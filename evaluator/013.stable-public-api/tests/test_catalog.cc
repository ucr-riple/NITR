#include <gtest/gtest.h>

#include <string>
#include <vector>

#include "library_catalog.h"

namespace {

std::vector<nitr::case013::Book> BuildBooks() {
  return {
      {"b1", "Atlas", "Ada", false},
      {"b2", "Archive of Fog", "Bea", true},
      {"b3", "Atomic Habits", "James Clear", false},
      {"b4", "A Tale of Two Cities", "Charles Dickens", false},
  };
}

}  // namespace

TEST(Case013Catalog, AvailableTitlesMatchPrefix) {
  nitr::case013::CatalogService service;
  const auto books = BuildBooks();
  EXPECT_EQ(service.FindAvailableTitles(books, "At"),
            (std::vector<std::string>{"Atlas", "Atomic Habits"}));

  const std::string digest = service.BuildCatalogDigest(books);
  EXPECT_EQ(digest.find("Archive of Fog"), std::string::npos);
  EXPECT_NE(digest.find("Atlas by Ada"), std::string::npos);
  EXPECT_NE(digest.find("Atomic Habits by James Clear"), std::string::npos);
}

TEST(Case013Catalog, DigestExcludesArchivedAndKeepsVisibleBooks) {
  nitr::case013::CatalogService service;
  const auto books = BuildBooks();

  const std::string digest = service.BuildCatalogDigest(books);
  EXPECT_TRUE(digest.find("Archive of Fog") == std::string::npos);
  EXPECT_TRUE(digest.find("Atlas by Ada") != std::string::npos);
  EXPECT_TRUE(digest.find("Atomic Habits by James Clear") != std::string::npos);
}
