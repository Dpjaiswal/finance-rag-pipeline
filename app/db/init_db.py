import logging

from app.core.config import get_settings
from app.db.seed import seed
from app.db.session import Base, engine
from app import models  # noqa: F401

logger = logging.getLogger(__name__)


def init_local_database() -> None:
    settings = get_settings()
    if not settings.database_url.startswith("sqlite"):
        return
    Base.metadata.create_all(bind=engine)
    seed()
    logger.info("Local SQLite database initialized")
