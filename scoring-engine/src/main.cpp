#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "scoring/scorer.hpp"

int main(int argc, char** argv) {
    scoring::Scorer scorer;
    if (argc > 1 && std::string(argv[1]) == "--stdin") {
        std::vector<scoring::ConceptInput> concepts;
        std::string line;
        while (std::getline(std::cin, line)) {
            if (line.empty()) continue;
            std::stringstream input(line);
            scoring::ConceptInput concept;
            int ready = 1;
            std::string difficulty;
            std::string progress;
            std::string readiness;
            if (!std::getline(input, concept.id, '|') || !std::getline(input, difficulty, '|') || !std::getline(input, progress, '|') || !std::getline(input, readiness)) return 2;
            concept.difficulty = std::stoi(difficulty);
            concept.progress = std::stod(progress);
            ready = std::stoi(readiness);
            concept.prerequisite_ready = ready != 0;
            concepts.push_back(concept);
        }
        for (const auto& score : scorer.rank(concepts)) std::cout << score.id << "|" << score.value << '\n';
        return 0;
    }
    const auto scores = scorer.rank({{"control-flow", 2, 35.0, true}, {"functions", 2, 0.0, true}, {"variables", 1, 100.0, true}});
    for (const auto& score : scores) std::cout << score.id << " " << score.value << '\n';
    return 0;
}
