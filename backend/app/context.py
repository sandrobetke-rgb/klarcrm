"""Kontext der aktuellen Anfrage (angemeldeter Benutzer) für Protokolle."""
from contextvars import ContextVar

current_user_id: ContextVar[int | None] = ContextVar("current_user_id", default=None)
