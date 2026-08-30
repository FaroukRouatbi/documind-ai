import logging

import structlog
from structlog.tracebacks import ExceptionDictTransformer

from app.core.config import settings


def get_shared_processors() -> list:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]


def configure_logging() -> None:
    shared_processors = get_shared_processors()

    if settings.environment == "prod":
        renderer = structlog.processors.JSONRenderer()
        # exception processor runs on the RENDER side, only at final formatting
        formatter_processors = [
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.ExceptionRenderer(ExceptionDictTransformer(show_locals=False)),
            renderer,
        ]
    else:
        renderer = structlog.dev.ConsoleRenderer()  # type: ignore[assignment]  # structlog renderers share no common base type
        formatter_processors = [
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=formatter_processors,   # type: ignore[arg-type]  # structlog processor typing is too strict
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
