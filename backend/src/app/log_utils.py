import logging.config

import structlog
from app.settings import get_settings

settings = get_settings()

shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
]

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": shared_processors,
        },
        "console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
            "foreign_pre_chain": shared_processors,
        },
    },
    "handlers": {
        "default": {
            "level": settings.LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "json" if settings.LOGS_AS_JSON else "console",
        },
        "opensearch": {
            "level": settings.LOG_LEVEL,
            "class": "opensearch_logger.OpenSearchHandler",
            "index_name": "logs",
            # "extra_fields": {"App": "test", "Environment": "dev"},
            "hosts": [{"host": "opensearch", "port": 9200}],
            "http_auth": ("admin", "admin"),
            "http_compress": True,
            "use_ssl": True,
            "verify_certs": False,
            "ssl_assert_hostname": False,
            "ssl_show_warn": False,
        }
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["default", "opensearch"], 
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["default", "opensearch"], 
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["default", "opensearch"], 
            "propagate": False,
        },
    },
}


def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.config.dictConfig(logging_config)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger('app').setLevel(logging.DEBUG)
    logging.getLogger('opensearch').setLevel(logging.ERROR)
