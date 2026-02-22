import sys
import logging
from pathlib import Path
sys.path.append('.')
from src.services.analyze import get_spectral_ceiling

data_dir = Path("tests/integration/data")
for flac in data_dir.glob("*.*"):
    if flac.suffix in ['.flac', '.opus', '.mp3', '.m4a']:
        ceiling = get_spectral_ceiling(flac)
        print(f"{flac.name}: {ceiling}")
