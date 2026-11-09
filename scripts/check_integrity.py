"""Check the file hashes shipped with this repository; Python standard library only."""
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = root / "SHA256SUMS"
checked = 0
for entry in manifest.read_text().splitlines():
    expected, relative = entry.split("  ", 1)
    file = (root / relative).resolve()
    if not file.is_relative_to(root) or not file.is_file():
        raise SystemExit(f"Missing or unsafe manifest path: {relative}")
    actual = hashlib.sha256(file.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"Checksum mismatch: {relative}")
    checked += 1
print(f"Verified {checked} file hashes.")
