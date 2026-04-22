import aiofiles
from pathlib import Path



class TextStorageService:
    BASE_DIR = Path("assets/clean_files")

    @staticmethod
    async def save_text(project_id: str, file_name: str, text: str) -> str:
        project_folder = TextStorageService.BASE_DIR / project_id
        project_folder.mkdir(parents=True, exist_ok=True)

        # clean name
        clean_name = Path(file_name).stem + "_clean.txt"
        file_path = project_folder / clean_name

        # NON-BLOCKING WRITE
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(text)

        return str(file_path)

    @staticmethod
    async def load_text(file_path: str) -> str:
        """
        Load text from a given file path asynchronously.
        Returns the file content as a string.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # NON-BLOCKING READ
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()

        return content