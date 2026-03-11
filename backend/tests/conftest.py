"""Pytest configuration and fixtures."""

import os

import pytest

# Set test env before any imports that read config
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Ensure test env vars for all tests."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
