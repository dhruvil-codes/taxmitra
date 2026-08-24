import os
import sys

# Ensure the backend/ directory is importable regardless of pytest invocation cwd.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Deterministic test environment: never touch the live API from tests.
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("OPENAI_API_KEY", "")

import pytest  # noqa: E402


@pytest.fixture()
def anyio_backend():
    return "asyncio"
