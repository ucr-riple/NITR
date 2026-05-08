#include "validator.h"

#include <gtest/gtest.h>

#include <string>

#include "grader.h"
#include "reporter.h"
#include "stats.h"
#include "submission.h"

TEST(ValidatorTest, RejectsEmptySubmissionContent) {
  nitr::case023::Submission submission;
  submission.student_id = "alice";
  submission.content = "";
  submission.is_late = false;

  nitr::case023::Validator validator;

  EXPECT_FALSE(validator.validate(submission));
}

TEST(ValidatorTest, RejectsLateSubmission) {
  nitr::case023::Submission submission;
  submission.student_id = "bob";
  submission.content = "complete answer";
  submission.is_late = true;

  nitr::case023::Validator validator;

  EXPECT_FALSE(validator.validate(submission));
}

TEST(ValidatorTest, AcceptsValidSubmission) {
  nitr::case023::Submission submission;
  submission.student_id = "carol";
  submission.content = "complete answer";
  submission.is_late = false;

  nitr::case023::Validator validator;

  EXPECT_TRUE(validator.validate(submission));
}

TEST(ValidatorTest, EmptyAndLateSubmissionIsRejected) {
  nitr::case023::Submission submission;
  submission.student_id = "dana";
  submission.content = "";
  submission.is_late = true;

  nitr::case023::Validator validator;

  EXPECT_FALSE(validator.validate(submission));
}

TEST(ValidationFlowTest, CallerUpdatesTotalProcessedOnlyForValidSubmissions) {
  nitr::case023::total_processed = 0;

  const nitr::case023::Submission submissions[] = {
      {"alice", "valid answer", false},
      {"bob", "", false},
      {"carol", "late answer", true},
      {"dana", "another valid answer", false},
  };

  nitr::case023::Validator validator;
  nitr::case023::Grader grader;

  for (const auto& submission : submissions) {
    if (!validator.validate(submission)) {
      continue;
    }

    ++nitr::case023::total_processed;
    (void)grader.Grade(submission);
  }

  EXPECT_EQ(nitr::case023::total_processed, 2);
}

TEST(ReporterTest, SummaryUsesGlobalProcessedCount) {
  nitr::case023::total_processed = 3;

  nitr::case023::Reporter reporter;

  EXPECT_EQ(reporter.Summary(), "Processed 3 submissions");
}

TEST(GraderTest, GradesSubmissionByContentLengthCappedAtOneHundred) {
  nitr::case023::Grader grader;

  nitr::case023::Submission short_submission;
  short_submission.content = "hello";

  EXPECT_EQ(grader.Grade(short_submission), 5);

  nitr::case023::Submission long_submission;
  long_submission.content = std::string(120, 'x');

  EXPECT_EQ(grader.Grade(long_submission), 100);
}
