import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMP_DIR = os.path.join(BASE_DIR, 'temp_files')
os.makedirs(TEMP_DIR, exist_ok=True)


class TempStorage:
    def __init__(self):
        pass

    def _get_file_path(self, shortcode: str) -> str:
        return os.path.join(TEMP_DIR, f"{shortcode}.bin")

    def create_entry(self, shortcode: str) -> None:
        """Create a new entry. No action needed for file-based storage."""
        pass

    def save_file(self, shortcode: str, file_data: bytes) -> None:
        file_path = self._get_file_path(shortcode)
        with open(file_path, "wb") as f:
            f.write(file_data)

    def get_file(self, shortcode: str) -> bytes | None:
        file_path = self._get_file_path(shortcode)
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return f.read()

    def delete_entry(self, shortcode: str) -> None:
        file_path = self._get_file_path(shortcode)
        if os.path.exists(file_path):
            os.remove(file_path)

    def exists(self, shortcode: str) -> bool:
        file_path = self._get_file_path(shortcode)
        return os.path.exists(file_path)


temp_storage = TempStorage()
