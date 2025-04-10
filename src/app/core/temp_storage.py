import os


TEMP_DIR = '/tmp/nutripeek_temp_storage'
os.makedirs(TEMP_DIR, exist_ok=True)


class TempStorage:
    def __init__(self):
        pass

    def _get_file_path(self, shortcode: str) -> str:
        return os.path.join(TEMP_DIR, f"{shortcode}.bin")

    def create_entry(self, shortcode: str):
        """Create a new entry. No action needed."""
        pass

    def save_file(self, shortcode: str, file_data: bytes):
        file_path = self._get_file_path(shortcode)
        with open(file_path, "wb") as f:
            f.write(file_data)

    def get_file(self, shortcode: str) -> bytes:
        file_path = self._get_file_path(shortcode)
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return f.read()

    def delete_entry(self, shortcode: str):
        file_path = self._get_file_path(shortcode)
        if os.path.exists(file_path):
            os.remove(file_path)

    def exists(self, shortcode: str) -> bool:
        return os.path.exists(self._get_file_path(shortcode))


temp_storage = TempStorage()
