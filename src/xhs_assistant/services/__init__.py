"""外部服务模块。"""
from __future__ import annotations

from xhs_assistant.services.rednote import RednoteClient, RednoteServiceError

__all__ = ["RednoteClient", "RednoteServiceError"]