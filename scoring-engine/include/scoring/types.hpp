#pragma once

#include <string>

namespace scoring {

struct ConceptInput {
    std::string id;
    int difficulty{1};
    double progress{0.0};
    bool prerequisite_ready{true};
};

struct Score {
    std::string id;
    double value{0.0};
};

}  // namespace scoring
