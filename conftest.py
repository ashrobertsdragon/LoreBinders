import pathlib
import sys

from loguru import logger

src_path = pathlib.Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

lorebinders_path = src_path / "lorebinders"
sys.path.insert(0, str(lorebinders_path))


def pytest_configure(config):
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level="DEBUG")


def pytest_unconfigure(config):
    logger.remove()  # Clean up handlers
