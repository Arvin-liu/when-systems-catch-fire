"""Offline, proposal-only V1 Goal intake preflight adapter."""

from .preflight import REPORT_SCHEMA, REQUEST_SCHEMA, evaluate_request

__all__ = ["REPORT_SCHEMA", "REQUEST_SCHEMA", "evaluate_request"]
