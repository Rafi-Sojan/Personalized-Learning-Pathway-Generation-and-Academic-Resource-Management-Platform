#include "scoring/scorer.hpp"

#include <algorithm>

namespace scoring {

Score Scorer::score(const ConceptInput& concept) const {
    const double gap = std::max(0.0, 100.0 - concept.progress);
    const double readiness = concept.prerequisite_ready ? 1.0 : 0.25;
    return {concept.id, (concept.difficulty * 20.0 + gap * 0.6) * readiness};
}

std::vector<Score> Scorer::rank(std::vector<ConceptInput> concepts) const {
    std::vector<Score> scores;
    scores.reserve(concepts.size());
    for (const auto& concept : concepts) scores.push_back(score(concept));
    std::sort(scores.begin(), scores.end(), [](const Score& left, const Score& right) { return left.value > right.value; });
    return scores;
}

}  // namespace scoring
