"""Utility package.

The initializer is intentionally dependency-light. Import concrete helpers from
their modules so logging/security code does not accidentally pull optional
OpenCV/image dependencies into the production web or inference containers.
"""

__all__: list[str] = []
