from __future__ import annotations

import os
from pathlib import Path

TEST_DB = Path(__file__).resolve().parents[1] / "data" / "test_cashira.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

import pytest

from scripts.seed import seed_database


@pytest.fixture(scope="session", autouse=True)
def seeded_database():
    seed_database(42)
    yield
