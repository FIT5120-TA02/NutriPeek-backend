import time


class TempStorage:
    def __init__(self):
        self._storage = {}

    def create_entry(self, shortcode: str):
        """Create a new shortcode entry"""
        self._storage[shortcode] = {"timestamp": time.time(), "file": None}

    def save_file(self, shortcode: str, file_data: bytes):
        """Save file data to the corresponding shortcode"""
        if shortcode in self._storage:
            self._storage[shortcode]["file"] = file_data

    def get_file(self, shortcode: str):
        """Get file data"""
        return self._storage.get(shortcode, {}).get("file")

    def delete_entry(self, shortcode: str):
        """Delete shortcode record"""
        if shortcode in self._storage:
            del self._storage[shortcode]

    def exists(self, shortcode: str) -> bool:
        """Check if shortcode exists"""
        return shortcode in self._storage


# Create a global singleton instance
temp_storage = TempStorage()
