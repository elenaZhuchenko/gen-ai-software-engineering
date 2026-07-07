import sys
import pathlib

import pytest
from fastapi.testclient import TestClient

# Ensure the app package is importable when pytest runs from repository root.
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from main import app  # FastAPI app at homework-2/src/main.py
import database


@pytest.fixture(autouse=True)
def clear_store():
    # Clear the in-memory store before each test
    database.store.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)

