import pytest

from src.config.settings import settings
from src.providers.factory import get_provider, reset_provider


def test_provider_requires_key():
    reset_provider()
    settings.openrouter_api_key = None
    with pytest.raises(ValueError):
        get_provider()
