#include <iostream>

#include "scoring/scorer.hpp"

int main() {
    scoring::Scorer scorer;
    const auto scores = scorer.rank({{"control-flow", 2, 35.0, true}, {"functions", 2, 0.0, true}, {"variables", 1, 100.0, true}});
    for (const auto& score : scores) std::cout << score.id << " " << score.value << '\n';
    return 0;
}
