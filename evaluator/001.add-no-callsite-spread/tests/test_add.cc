#include <gtest/gtest.h>

#include <cmath>

#include "add.h"

TEST(Add, IntAddWorks) {
  EXPECT_EQ(nitr::case001::add(3, 4), 7);
  EXPECT_EQ(nitr::case001::add(0, 0), 0);
  EXPECT_EQ(nitr::case001::add(-3, 4), 1);
}

TEST(Add, FloatAddWorks) {
  EXPECT_EQ(nitr::case001::add(3.5, 4.5), 8.0);
  EXPECT_EQ(nitr::case001::add(-1.25, 2.0), 0.75);
  EXPECT_NEAR(nitr::case001::add(0.1, 0.2), 0.3, 1e-12);
}

TEST(Add, DoubleAddWorks) {
  EXPECT_EQ(nitr::case001::add(3.5, 4.5), 8.0);
  EXPECT_EQ(nitr::case001::add(-1.25, 2.0), 0.75);
  EXPECT_NEAR(nitr::case001::add(0.1, 0.2), 0.3, 1e-12);
  EXPECT_NEAR(nitr::case001::add(100000000.0, 1.0), 100000001.0, 1e-12);
}

TEST(Add, LongLongAddWorks) {
  EXPECT_EQ(nitr::case001::add(1e100, 1e100), 2e100);
  EXPECT_EQ(nitr::case001::add(1e100, -2e100), -1e100);
}
