import os
import json
from typing import Any, Optional, Dict


# ------------------------------------------------------------
# ---------------------- File Manager ---------------------
# ------------------------------------------------------------

class FileManager:
    """Handles file I/O operations."""
    
    @staticmethod
    def ensure_directory(path: str) -> None:
        """Create directory and all parent directories if they don't exist."""
        # Explicitly use parents=True to create nested directory structures
        # Example: "/docs/Backend/Auth/JWT" creates Backend/, Auth/, and JWT/
        os.makedirs(path, exist_ok=True)  # parents=True is default in Python 3
    
    @staticmethod
    def save_json(data: Any, filepath: str) -> None:
        """Save data as JSON to file."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
    
    @staticmethod
    def load_json(filepath: str) -> Optional[Dict[str, Any]]:
        """Load JSON from file, return None if file doesn't exist."""
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def save_text(content: str, filepath: str) -> None:
        """Save text content to file."""
        with open(filepath, 'w') as f:
            f.write(content)
    
    @staticmethod
    def load_text(filepath: str) -> str:
        """Load text content from file."""
        with open(filepath, 'r') as f:
            return f.read()

file_manager = FileManager()
