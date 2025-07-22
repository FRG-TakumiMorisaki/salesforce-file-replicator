import os
from pathlib import Path


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_unique_filename(directory: Path, filename: str) -> Path:
    target = directory / filename
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    counter = 1
    while True:
        new_name = f"{stem}({counter}){suffix}"
        new_path = directory / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def save_file(directory: Path, filename: str, data: bytes) -> Path:
    ensure_directory(directory)
    path = get_unique_filename(directory, filename)
    with open(path, 'wb') as f:
        f.write(data)
    return path
