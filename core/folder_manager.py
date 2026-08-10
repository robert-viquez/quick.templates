import re
import shutil
from pathlib import Path
from PySide6.QtWidgets import QInputDialog
from qfluentwidgets import InfoBar, InfoBarPosition

class FolderService:
    INVALID_WINDOWS_NAMES = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    def __init__(self, base_directory: Path) -> None:
        self.base_directory = base_directory
        
    def get_folders(self) -> list[Path]:
        if not self.base_directory.exists():
            return []

        return sorted(
            [
                path
                for path in self.base_directory.rglob("*")
                if path.is_dir()
            ],
            key=lambda path: str(path).casefold(),
        )

    def create_folder(
        self,
        name: str,
        parent: Path | None = None,
    ) -> Path:
        sanitized_name = self.validate_folder_name(name)

        target_parent = parent or self.base_directory
        target_parent = target_parent.resolve()

        self.ensure_inside_base_directory(target_parent)

        folder_path = target_parent / sanitized_name

        if folder_path.exists():
            raise FileExistsError(
                f"La carpeta '{sanitized_name}' ya existe."
            )

        folder_path.mkdir(parents=False, exist_ok=False)

        return folder_path

    def delete_folder(
        self,
        folder_path: Path,
        recursive: bool = False,
    ) -> None:
        folder_path = folder_path.resolve()

        self.ensure_inside_base_directory(folder_path)

        if folder_path == self.base_directory.resolve():
            raise ValueError(
                "No se puede eliminar la carpeta principal."
            )

        if not folder_path.exists():
            raise FileNotFoundError(
                "La carpeta seleccionada no existe."
            )

        if not folder_path.is_dir():
            raise NotADirectoryError(
                "La ruta seleccionada no es una carpeta."
            )

        has_contents = any(folder_path.iterdir())

        if has_contents and not recursive:
            raise OSError(
                "La carpeta no está vacía."
            )

        if recursive:
            shutil.rmtree(folder_path)
        else:
            folder_path.rmdir()

    def validate_folder_name(self, name: str) -> str:
        cleaned_name = name.strip()

        if not cleaned_name:
            raise ValueError(
                "El nombre de la carpeta no puede estar vacío."
            )

        if cleaned_name.upper() in self.INVALID_WINDOWS_NAMES:
            raise ValueError(
                "Ese nombre está reservado por Windows."
            )

        if re.search(r'[<>:"/\\|?*]', cleaned_name):
            raise ValueError(
                "El nombre contiene caracteres no permitidos."
            )

        if cleaned_name.endswith(".") or cleaned_name.endswith(" "):
            raise ValueError(
                "El nombre no puede terminar en punto o espacio."
            )

        return cleaned_name

    def ensure_inside_base_directory(
        self,
        path: Path,
    ) -> None:
        base = self.base_directory.resolve()
        resolved_path = path.resolve()

        try:
            resolved_path.relative_to(base)
        except ValueError as error:
            raise PermissionError(
                "La ruta está fuera de la carpeta principal."
            ) from error