import os
import json
import csv
import re
import zipfile
from loguru import logger
from typing import Optional, Dict, Any, List

from app.config import settings


class StorageService:
    def __init__(self):
        self.storage_dir = settings.unloading_data_dir

    async def unload_data_to_file(
        self, file_name: str, ext: str, data: List[List[str]]
    ) -> Optional[Dict[str, Any]]:
        try:
            if len(data) == 0:
                return None

            file_name = StorageService.normalize_filename(file_name)
            file_name += f'.{ext}'
            file_path = os.path.join(self.storage_dir, file_name)
            media_type = None

            if ext == "json":
                if not os.path.exists(file_path):
                    with open(file_path, 'w') as f:
                        json.dump(data, f)
                        media_type = 'application/json'
                else:
                    media_type = 'application/json'

            elif ext == "csv":
                if not os.path.exists(file_path):
                    with open(file_path, 'w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerows(data)
                        media_type = 'text/csv'

                else:
                    media_type = 'text/csv'

            if media_type:
                return {
                    "path": file_path,
                    "media_type": media_type,
                    "filename": file_name
                }

            logger.error(f"Unsupported file extension: {ext}")
            return None

        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error writing data to file: {e}")
            return None

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None

    @staticmethod
    def normalize_filename(input_string: str) -> str:
        normalized = input_string.lower()
        normalized = re.sub(r'[^a-z0-9_]', '_', normalized)
        normalized = re.sub(r'_{2,}', '_', normalized)
        normalized = normalized.strip('_')
        return normalized[:30]

    async def unload_files_to_packs(
        self, file_name: str, ext: str, files: List[str]
    ) -> Optional[Dict[str, Any]]:
        try:
            if len(files) == 0:
                return None

            file_name = StorageService.normalize_filename(file_name)
            file_name += f'.{ext}'
            file_path = os.path.join(self.storage_dir, file_name)

            media_type = None

            if ext == "zip":
                if not os.path.exists(file_path):
                    with zipfile.ZipFile(file_path, 'w') as zipf:
                        for file in files:
                            zipf.write(
                                os.path.join(self.storage_dir, file),
                                arcname=file
                            )
                        media_type = 'application/zip'
                else:
                    media_type = 'application/zip'

            if media_type:
                return {
                    "path": file_path,
                    "media_type": media_type,
                    "filename": file_name
                }

            logger.error(f"Unsupported file extension: {ext}")
            return None

        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error writing data to file: {e}")
            return None

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
