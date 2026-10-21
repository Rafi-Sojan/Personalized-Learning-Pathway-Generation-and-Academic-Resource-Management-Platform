"""Development seed entry point; production deployments should run migrations first."""

from app.repositories.in_memory import repository


if __name__ == "__main__":
    print(f"Loaded {len(repository.courses)} courses and {len(repository.concepts)} concepts")
