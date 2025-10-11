from pathlib import Path

def cleanup_files(*files: Path):
    for f in files:
        if f and f.exists():
            f.unlink(missing_ok=True)