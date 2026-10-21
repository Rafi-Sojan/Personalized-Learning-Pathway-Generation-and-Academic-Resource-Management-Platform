# Logical data model

```mermaid
erDiagram
  COURSES ||--o{ CONCEPTS : contains
  CONCEPTS ||--o{ RESOURCES : explains
  USERS ||--o{ PROGRESS : records
  CONCEPTS ||--o{ PROGRESS : tracks
```
