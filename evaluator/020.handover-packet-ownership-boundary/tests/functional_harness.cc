#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

#include "handover_packet_preview.h"
#include "handover_packet_writer.h"
#include "shift_tracker.h"

namespace {

std::string ReadFile(const std::string& path) {
  std::ifstream input(path);
  if (!input) {
    throw std::runtime_error("failed to read file: " + path);
  }
  std::ostringstream buffer;
  buffer << input.rdbuf();
  return buffer.str();
}

std::string JsonEscape(const std::string& value) {
  std::string escaped;
  escaped.reserve(value.size() + 8);
  for (char ch : value) {
    switch (ch) {
      case '\\':
        escaped += "\\\\";
        break;
      case '"':
        escaped += "\\\"";
        break;
      case '\n':
        escaped += "\\n";
        break;
      default:
        escaped += ch;
        break;
    }
  }
  return escaped;
}

nitr::case020::ShiftTracker BuildInProgressTracker() {
  nitr::case020::ShiftTracker tracker("SHIFT-500");
  tracker.AddCompletedTote("TOTE-100", 4);
  tracker.AddCompletedTote("TOTE-101", 3);
  tracker.StartTote("TOTE-102");
  tracker.ScanPackagesIntoCurrentTote(2);
  return tracker;
}

nitr::case020::ShiftTracker BuildClosedTracker() {
  nitr::case020::ShiftTracker tracker("SHIFT-501");
  tracker.AddCompletedTote("TOTE-200", 5);
  tracker.AddCompletedTote("TOTE-201", 1);
  tracker.StartTote("TOTE-202");
  tracker.ScanPackagesIntoCurrentTote(2);
  tracker.CloseCurrentTote();
  return tracker;
}

void PrintSingleOutputCase(const std::string& scenario_name,
                           nitr::case020::ShiftTracker tracker,
                           const std::string& output_path) {
  const std::string preview =
      nitr::case020::BuildHandoverPacketPreview(tracker);
  const nitr::case020::HandoverPacket packet =
      nitr::case020::SaveHandoverPacket(tracker, output_path);
  const std::string saved = ReadFile(output_path);

  std::cout << "{";
  std::cout << "\"scenario\":\"" << scenario_name << "\",";
  std::cout << "\"preview\":\"" << JsonEscape(preview) << "\",";
  std::cout << "\"saved\":\"" << JsonEscape(saved) << "\",";
  std::cout << "\"row_count\":" << packet.rows.size() << ",";
  std::cout << "\"tote_count\":" << packet.summary.tote_count << ",";
  std::cout << "\"package_count\":" << packet.summary.package_count << ",";
  std::cout << "\"last_row_in_progress\":"
            << ((packet.rows.empty() ||
                 !packet.rows.back().from_in_progress_tote)
                    ? "false"
                    : "true");
  std::cout << "}";
}

void PrintSequenceCase(const std::string& output_path_a,
                       const std::string& output_path_b) {
  nitr::case020::ShiftTracker tracker = BuildInProgressTracker();

  const std::string preview_first =
      nitr::case020::BuildHandoverPacketPreview(tracker);
  const nitr::case020::HandoverPacket packet_first =
      nitr::case020::SaveHandoverPacket(tracker, output_path_a);
  const std::string saved_first = ReadFile(output_path_a);
  const std::string preview_second =
      nitr::case020::BuildHandoverPacketPreview(tracker);
  const nitr::case020::HandoverPacket packet_second =
      nitr::case020::SaveHandoverPacket(tracker, output_path_b);
  const std::string saved_second = ReadFile(output_path_b);

  std::cout << "{";
  std::cout << "\"scenario\":\"sequence\",";
  std::cout << "\"preview_first\":\"" << JsonEscape(preview_first) << "\",";
  std::cout << "\"preview_second\":\"" << JsonEscape(preview_second) << "\",";
  std::cout << "\"saved_first\":\"" << JsonEscape(saved_first) << "\",";
  std::cout << "\"saved_second\":\"" << JsonEscape(saved_second) << "\",";
  std::cout << "\"row_count_first\":" << packet_first.rows.size() << ",";
  std::cout << "\"row_count_second\":" << packet_second.rows.size() << ",";
  std::cout << "\"package_count_first\":" << packet_first.summary.package_count
            << ",";
  std::cout << "\"package_count_second\":"
            << packet_second.summary.package_count;
  std::cout << "}";
}

}  // namespace

int main(int argc, char** argv) {
  if (argc < 3) {
    std::cerr << "usage: functional_harness <scenario> <output_path_a> "
                 "[output_path_b]\n";
    return 1;
  }

  const std::string scenario = argv[1];
  const std::string output_path_a = argv[2];

  try {
    if (scenario == "with_in_progress") {
      PrintSingleOutputCase(scenario, BuildInProgressTracker(), output_path_a);
      return 0;
    }

    if (scenario == "without_in_progress") {
      PrintSingleOutputCase(scenario, BuildClosedTracker(), output_path_a);
      return 0;
    }

    if (scenario == "sequence") {
      if (argc < 4) {
        std::cerr << "sequence scenario requires two output paths\n";
        return 1;
      }
      PrintSequenceCase(output_path_a, argv[3]);
      return 0;
    }
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\n";
    return 1;
  }

  std::cerr << "unknown scenario: " << scenario << "\n";
  return 1;
}
