import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SuppressSentryShutdownFilter(logging.Filter):
    def filter(self, record):
        return not any(
            msg in record.getMessage()
            for msg in [
                "atexit: got shutdown signal",
                "atexit: shutting down client",
                "Flushing HTTP transport",
                "Sending envelope",
                "background worker got flush request",
                "event(s) pending on flush",
                "background worker flushed",
                "Killing HTTP transport",
                "background worker got kill request",
            ]
        )

def init_sentry():
    if not settings.SENTRY_DSN:
        logger.warning("SENTRY_DSN not configured, Sentry will not be initialized")
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.CRITICAL)
        ],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
        before_send=lambda event, hint: None if "http 4" in str(event.get("exception", "")).lower() else event
    )
    logger.info("Sentry initialized successfully")