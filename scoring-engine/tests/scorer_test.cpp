#include <cassert>

#include "scoring/scorer.hpp"

// Assert that a high learning gap receives a positive, expected priority score.
int main() {
    scoring::Scorer scorer;
    const auto score = scorer.score({"functions", 2, 0.0, true});
    assert(score.value == 100.0);
    return 0;
}
