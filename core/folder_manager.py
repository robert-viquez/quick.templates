import re
import shutil
from pathlib import Path


class FolderService:
    INVALID_WINDOWS_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}

    def __init__(self, base_directory: Path) -> None:
        self.base_directory = base_directory.resolve()

    def get_folders(self) -> list[Path]:
        if not self.base_directory.exists():
            return []
        return sorted((p for p in self.base_directory.rglob("*") if p.is_dir()), key=lambda p: str(p).casefold())

    def create_folder(self, name: str, parent: Path | None = None) -> Path:
        name = self.validate_folder_name(name)
        parent = (parent or self.base_directory).resolve()
        self.ensure_inside_base_directory(parent)
        target = parent / name
        target.mkdir(parents=False, exist_ok=False)
        return target

    def rename_folder(self, folder: Path, name: str) -> Path:
        folder = folder.resolve()
        self.ensure_inside_base_directory(folder)
        if folder == self.base_directory:
            raise ValueError("No se puede renombrar la carpeta principal.")
        target = folder.with_name(self.validate_folder_name(name))
        self.ensure_inside_base_directory(target)
        if target.exists():
            raise FileExistsError("Ya existe una carpeta con ese nombre.")
        return folder.rename(target)

    def delete_folder(self, folder: Path, recursive: bool = False) -> None:
        folder = folder.resolve()
        self.ensure_inside_base_directory(folder)
        if folder == self.base_directory:
            raise ValueError("No se puede eliminar la carpeta principal.")
        if recursive:
            shutil.rmtree(folder)
        else:
            folder.rmdir()

    def validate_folder_name(self, name: str) -> str:
        name = name.strip()
        if not name or name.upper() in self.INVALID_WINDOWS_NAMES or re.search(r'[<>:"/\\|?*]', name) or name.endswith((".", " ")):
            raise ValueError("El nombre de carpeta no es válido.")
        return name

    def ensure_inside_base_directory(self, path: Path) -> None:
        try:
            path.resolve().relative_to(self.base_directory)
        except ValueError as error:
            raise PermissionError("La ruta está fuera de la carpeta principal.") from error
