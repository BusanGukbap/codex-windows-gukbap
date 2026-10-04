import shutil
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent))

FIXTURES = TESTS / "fixtures"


@pytest.fixture
def wiki(tmp_path: Path) -> Path:
    """A fresh copy of the clean fixture wiki."""
    root = tmp_path / "wiki-root"
    shutil.copytree(FIXTURES / "clean", root)
    return root.resolve()
