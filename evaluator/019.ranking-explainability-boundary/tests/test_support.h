#ifndef CASE019_EVALUATOR_TEST_SUPPORT_H_
#define CASE019_EVALUATOR_TEST_SUPPORT_H_

#include <cstdlib>
#include <iostream>
#include <string>
#include <type_traits>
#include <utility>

namespace case019_test {

inline void Fail(const std::string& message) {
  std::cerr << message << "\n";
  std::exit(1);
}

inline void Expect(bool condition, const std::string& message) {
  if (!condition) {
    Fail(message);
  }
}

template <typename T, typename = void>
struct has_reason_summary : std::false_type {};

template <typename T>
struct has_reason_summary<
    T, std::void_t<decltype(std::declval<T>().reason_summary)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_summary_final_score : std::false_type {};

template <typename T>
struct has_summary_final_score<
    T, std::void_t<decltype(std::declval<T>().final_score)>> : std::true_type {
};

template <typename T, typename = void>
struct has_summary_positive : std::false_type {};

template <typename T>
struct has_summary_positive<
    T, std::void_t<decltype(std::declval<T>().strongest_positive)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_summary_negative : std::false_type {};

template <typename T>
struct has_summary_negative<
    T, std::void_t<decltype(std::declval<T>().strongest_negative)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_inspect_method : std::false_type {};

template <typename T>
struct has_inspect_method<
    T, std::void_t<decltype(std::declval<const T>().Inspect(
           std::declval<const std::vector<nitr::case019::Item>&>(), 0))>>
    : std::true_type {};

template <typename T, typename = void>
struct has_compare_method : std::false_type {};

template <typename T>
struct has_compare_method<
    T, std::void_t<decltype(std::declval<const T>().Compare(
           std::declval<const std::vector<nitr::case019::Item>&>(), 0, 0))>>
    : std::true_type {};

template <typename T, typename = void>
struct has_status_field : std::false_type {};

template <typename T>
struct has_status_field<T, std::void_t<decltype(std::declval<T>().status)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_inspection_score : std::false_type {};

template <typename T>
struct has_inspection_score<
    T, std::void_t<decltype(std::declval<T>().final_score)>> : std::true_type {
};

template <typename T, typename = void>
struct has_inspection_positive : std::false_type {};

template <typename T>
struct has_inspection_positive<
    T, std::void_t<decltype(std::declval<T>().strongest_positive)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_inspection_negative : std::false_type {};

template <typename T>
struct has_inspection_negative<
    T, std::void_t<decltype(std::declval<T>().strongest_negative)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_lost_on_tie_break : std::false_type {};

template <typename T>
struct has_lost_on_tie_break<
    T, std::void_t<decltype(std::declval<T>().lost_on_tie_break)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_tie_break_against_id : std::false_type {};

template <typename T>
struct has_tie_break_against_id<
    T, std::void_t<decltype(std::declval<T>().tie_break_against_id)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_winner_id : std::false_type {};

template <typename T>
struct has_winner_id<T, std::void_t<decltype(std::declval<T>().winner_id)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_loser_id : std::false_type {};

template <typename T>
struct has_loser_id<T, std::void_t<decltype(std::declval<T>().loser_id)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_decided_by_tie_break : std::false_type {};

template <typename T>
struct has_decided_by_tie_break<
    T, std::void_t<decltype(std::declval<T>().decided_by_tie_break)>>
    : std::true_type {};

template <typename T, typename = void>
struct has_decisive_reason : std::false_type {};

template <typename T>
struct has_decisive_reason<
    T, std::void_t<decltype(std::declval<T>().decisive_reason)>>
    : std::true_type {};

}  // namespace case019_test

#endif  // CASE019_EVALUATOR_TEST_SUPPORT_H_
