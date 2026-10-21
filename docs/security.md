# Security baseline

The skeleton keeps authentication intentionally simple for local development. Before production, replace demo tokens with short-lived JWTs, hash passwords with Argon2 or bcrypt, validate uploaded file types and sizes, add request rate limiting at the edge, and move secrets to a managed secret store.
