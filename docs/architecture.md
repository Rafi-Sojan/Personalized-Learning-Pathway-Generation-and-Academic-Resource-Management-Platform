# Architecture

The platform is split into four deployable concerns:

1. React/Vite presents courses, concept maps, roadmaps, resources, quizzes, and progress.
2. FastAPI owns the HTTP contract and application services.
3. The ML package provides deterministic, testable preprocessing, mapping, graph, and scheduling primitives.
4. The C++ scoring engine provides a fast ranking primitive that can later be exposed over a service boundary.

The current API uses an in-memory repository so a new developer can run the vertical slice without provisioning infrastructure.
