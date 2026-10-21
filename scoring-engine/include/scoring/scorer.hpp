#pragma once

#include <vector>

#include "scoring/types.hpp"

namespace scoring {

class Scorer {
public:
    Score score(const ConceptInput& concept) const;
    std::vector<Score> rank(std::vector<ConceptInput> concepts) const;
};

}  // namespace scoring
