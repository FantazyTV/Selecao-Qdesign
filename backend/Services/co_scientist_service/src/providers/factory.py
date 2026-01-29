from .openrouter_provider import OpenRouterProvider


_provider = None


def get_provider():
    global _provider
    if _provider is None:
        _provider = OpenRouterProvider()
    return _provider


def reset_provider() -> None:
    global _provider
    _provider = None
