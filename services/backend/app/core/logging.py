"""
Structured logging configuration for the Argus backend.

In development: pretty colored console output for humans.
In production/test: JSON output for Loki ingestion and field-level querying.
"""

import logging

import structlog


def configure_logging(environment: str, log_level: str = "info"):
    """Configure structlog and stdlib logging for the given environment."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if environment == "development":
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
    )

    # Capture stdlib logging (uvicorn, SQLAlchemy) into the same format
    logging.basicConfig(level=level, format="%(message)s")
