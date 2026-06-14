#include <gtest/gtest.h>

#include <string>
#include <vector>

#include "applicant.h"
#include "audit_logger.h"
#include "loan_policy.h"
#include "loan_review_service.h"

namespace {

class MemoryAuditLogger final : public nitr::case010::AuditLogger {
 public:
  void Log(const std::string& message) override {
    messages.push_back(message);
  }

  std::vector<std::string> messages;
};

}  // namespace

TEST(Case010LoanReview, ApprovesEligibleApplicant) {
  const nitr::case010::Applicant applicant{"alice", 750, 90000, 0.20};
  const nitr::case010::ReviewDecision decision =
      nitr::case010::EvaluateApplicant(applicant);

  EXPECT_TRUE(decision.approved);
  EXPECT_TRUE(decision.denial_reasons.empty());
}

TEST(Case010LoanReview, ReturnsOrderedDenialReasons) {
  const nitr::case010::Applicant applicant{"carol", 680, 40000, 0.45};
  const nitr::case010::ReviewDecision decision =
      nitr::case010::EvaluateApplicant(applicant);

  EXPECT_FALSE(decision.approved);
  EXPECT_EQ(decision.denial_reasons.size(), 3u);
  EXPECT_EQ(decision.denial_reasons[0], "low_credit");
  EXPECT_EQ(decision.denial_reasons[1], "low_income");
  EXPECT_EQ(decision.denial_reasons[2], "high_debt");
}

TEST(Case010LoanReview, ReviewBatchCollectsApprovedIdsAndAuditMessages) {
  const std::vector<nitr::case010::Applicant> applicants = {
      {"alice", 750, 90000, 0.20},
      {"bob", 650, 80000, 0.30},
      {"carol", 710, 40000, 0.45},
  };

  MemoryAuditLogger logger;
  const nitr::case010::ReviewBatchResult result =
      nitr::case010::ReviewApplicants(applicants, &logger);

  ASSERT_EQ(result.approved_ids.size(), 1u);
  EXPECT_EQ(result.approved_ids[0], "alice");

  ASSERT_EQ(logger.messages.size(), 3u);
  EXPECT_EQ(logger.messages[0], "alice approved");
  EXPECT_EQ(logger.messages[1], "bob denied: low_credit");
  EXPECT_EQ(logger.messages[2], "carol denied: low_income,high_debt");
}
