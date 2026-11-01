import logging


def configure_logging() -> None:
    """Install structured application logging with the configured verbosity and format."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
