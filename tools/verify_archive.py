from pathlib import Path
import hashlib
root = Path(__file__).resolve().parents[1]
n = 0
for line in (root / "MANIFEST.sha256").read_text().splitlines():
    digest, rel = line.split("  ", 1)
    p = root / rel
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    assert h.hexdigest() == digest, rel
    n += 1
print(f"PASS: {n} files")
