"""Shared storage helpers."""

from pathlib import Path
import json

class StorageManager:

    @staticmethod
    def ensure_dir(path: Path):

        path.mkdir(
            parents=True,
            exist_ok=True
        )

    @staticmethod
    def load_json(
        file_path: Path,
        default=None
    ):

        if default is None:
            default = {}

        if not file_path.exists():
            return default

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception: # pylint: disable=broad-exception-caught

            return default

    @staticmethod
    def save_json(
        file_path: Path,
        data
    ):

        temp_file = (
            file_path
            .with_suffix(".tmp")
        )

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

        temp_file.replace(
            file_path
        )
