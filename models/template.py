from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Template:
    title: str
    content: str
    path: Path
    folder: str