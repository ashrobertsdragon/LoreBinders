import pathlib
import sys

src_path = pathlib.Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

lorebinders_path = src_path / "lorebinders"
sys.path.insert(0, str(lorebinders_path))
