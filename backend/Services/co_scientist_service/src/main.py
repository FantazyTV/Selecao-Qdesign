import logging.config
from pathlib import Path
import yaml
from fastapi import FastAPI

from .api.routes import router


def _configure_logging():
    config_path = Path(__file__).parent / "config" / "logging.yaml"
    with config_path.open("r", encoding="utf-8") as handle:
        logging.config.dictConfig(yaml.safe_load(handle))


_configure_logging()
app = FastAPI(title="Co-Scientist Service")
app.include_router(router)
