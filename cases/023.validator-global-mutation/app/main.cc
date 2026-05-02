#include <iostream>
#include <vector>

#include "grader.h"
#include "reporter.h"
#include "stats.h"
#include "submission.h"
#include "validator.h"

int main() {
    using namespace nitr::case023;

    const std::vector<Submission> submissions = {
        {"alice", "Well-structured solution", false},
        {"bob", "", false},
        {"carol", "Late but complete", true},
        {"dana", "Concise answer", false},
    };

    Grader grader;
    Validator validator;

    for (const Submission& submission : submissions) {
        if (!validator.validate(submission)) {
            continue;
        }

        ++total_processed;
        std::cout << submission.student_id << ": " << grader.Grade(submission) << '\n';
    }

    Reporter reporter;
    std::cout << reporter.Summary() << '\n';
    return 0;
}
