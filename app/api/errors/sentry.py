import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from app.core.config import settings

def init_sentry():
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        environment="development"  
    )