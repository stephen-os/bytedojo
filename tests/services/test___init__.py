"""Tests for the services package's public exports."""

import bytedojo.services as services


def test_public_exports_are_importable():
    """The names listed in __all__ all resolve on the package."""
    for name in services.__all__:
        assert hasattr(services, name), f"services.__all__ promises {name!r}"


def test_service_classes_are_constructible():
    """Each *Service class can be instantiated with no args (DI by call site)."""
    services.FetchService()
    services.PickService()
    services.GradingService()
    services.ReviewService()
