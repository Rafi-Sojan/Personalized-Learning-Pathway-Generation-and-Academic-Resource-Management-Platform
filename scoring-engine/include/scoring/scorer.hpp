#pragma once

#include <vector>

#include "scoring/types.hpp"

namespace scoring {

class Scorer {
public:
    /// Compute a priority score from difficulty, progress gap, and prerequisite readiness.
    Score score(const ConceptInput& concept) const;
    /// Return all concepts sorted from highest to lowest priority score.
    std::vector<Score> rank(std::vector<ConceptInput> concepts) const;
};

}  // namespace scoring
