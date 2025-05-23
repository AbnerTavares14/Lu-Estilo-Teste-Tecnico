import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def init_sentry():
    if not settings.SENTRY_DSN:
        logger.warning("SENTRY_DSN not configured, Sentry will not be initialized")
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
        ],
        traces_sample_rate=1.0,
        environment="development",
        debug=True
    )
    logger.info("Sentry initialized successfully")