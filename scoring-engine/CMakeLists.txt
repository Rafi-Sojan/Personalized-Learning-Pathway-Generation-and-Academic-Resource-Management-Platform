cmake_minimum_required(VERSION 3.20)
project(learning_scoring LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(scoring src/scorer.cpp)
target_include_directories(scoring PUBLIC include)

add_executable(scoring-cli src/main.cpp)
target_link_libraries(scoring-cli PRIVATE scoring)

enable_testing()
add_executable(scoring-tests tests/scorer_test.cpp)
target_link_libraries(scoring-tests PRIVATE scoring)
add_test(NAME scoring-tests COMMAND scoring-tests)
