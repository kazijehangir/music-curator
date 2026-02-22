import subprocess
import mutagen

file_path = "/home/jehangir/music-curator/tests/integration/data/1. aleemrk - Hasrat.flac"
p = subprocess.run([
    "/home/jehangir/music-curator/.venv/bin/beet",
    "import", "-q", "-C", "-s", file_path
], capture_output=True, text=True)
print("OUT:", p.stdout)
print("ERR:", p.stderr)
f = mutagen.File(file_path)
print("Tags:", f.tags)
