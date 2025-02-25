import os
import json
import logging
import csv
from typing import Optional, Dict, Any, List

from app.config import settings


class StorageService:
    def __init__(self):
        self.storage_dir = settings.unloading_data_dir

    async def unload_data_to_file(
        self, file_name: str, data: List[List[str]]
    ) -> Optional[Dict[str, Any]]:
        try:
            file_path = os.path.join(self.storage_dir, file_name)
            media_type = None
            _, ext = os.path.splitext(file_name)

            if ext == ".json":
                if not os.path.exists(file_path):
                    with open(file_path, 'w') as f:
                        json.dump(data, f)
                        logging.info(
                            f"Data successfully written to {file_path}"
                        )
                        media_type = 'application/json'
                else:
                    logging.warning(
                        f"File {file_path} already exists. Data not written."
                    )
                    media_type = 'application/json'

            elif ext == ".csv":
                if not os.path.exists(file_path):
                    with open(file_path, 'w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerows(data)
                        logging.info(
                            f"Data successfully written to {file_path}"
                        )
                        media_type = 'text/csv'

                else:
                    logging.warning(
                        f"File {file_path} already exists. Data not written.")
                    media_type = 'text/csv'

            if media_type:
                return {
                    "path": file_path,
                    "media_type": media_type,
                    "filename": file_name
                }

            logging.error(f"Unsupported file extension: {ext}")
            return None

        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Error writing data to file: {e}")
            return None

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None
