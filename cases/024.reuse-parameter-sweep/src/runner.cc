#include "runner.h"
#include <cmath>
#include <cstdint>
#include <stdexcept>

namespace nitr::case024 {

TrialResult run_trial(const TrialParams& p) {
  if (p.learning_rate <= 0.0) {
    throw std::invalid_argument("learning_rate must be positive");
  }
  if (p.batch_size <= 0) {
    throw std::invalid_argument("batch_size must be positive");
  }
  if (p.warmup_steps < 0) {
    throw std::invalid_argument("warmup_steps must be non-negative");
  }

  // Seeded xorshift32 for deterministic per-trial noise.
  uint32_t state = static_cast<uint32_t>(p.seed) ^ 0xDEADBEEFu;
  state ^= static_cast<uint32_t>(p.batch_size) * 2654435761u;
  state ^= static_cast<uint32_t>(p.warmup_steps + 1) * 40503u;
  state ^= static_cast<uint32_t>(p.learning_rate * 1'000'000.0) * 0x9E3779B9u;
  if (state == 0u) { state = 1u; }

  state ^= state << 13;
  state ^= state >> 17;
  state ^= state << 5;

  const double noise =
      (static_cast<double>(state & 0x00FFFFFFu) /
       static_cast<double>(0x01000000u) - 0.5) * 0.08;

  // Synthetic loss: lower learning_rate and fewer warmup steps yield higher loss.
  const double base_loss =
      1.0 / (p.learning_rate *
             std::log1p(static_cast<double>(p.warmup_steps) + 1.0)) +
      std::log1p(static_cast<double>(p.batch_size)) * 0.04;

  return TrialResult{base_loss + noise};
}

}  // namespace nitr::case024
