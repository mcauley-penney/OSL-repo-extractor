"""Output writing tools for batch repository extraction."""

from __future__ import annotations

from copy import deepcopy
import json
from json.decoder import JSONDecodeError
import os
from pathlib import Path
import tempfile


class OutputDataError(ValueError):
    """Raised when existing output data cannot be safely merged."""


def build_repo_output_chunk(repo_slug: str, repo_data: dict) -> dict:
    """
    Build a top-level output chunk for one repository.

    Args:
        repo_slug (str): canonical GitHub repository slug in owner/name form.
        repo_data (dict): extracted data keyed by issue or PR number.

    Returns:
        dict: repo-scoped output chunk ready to merge into the output file.
    """
    return {repo_slug: deepcopy(repo_data)}


def merge_output_chunks(base_dict: dict, add_dict: dict) -> dict:
    """
    Recursively merge two output dictionaries and return the merged result.

    Nested dictionaries are merged in place so repeated writes may extend
    existing repo namespaces without overwriting unrelated data.
    """
    merged_dict = deepcopy(base_dict)
    _merge_dicts_recursive(merged_dict, add_dict)

    return merged_dict


class OutputWriter:
    """Read, merge, and atomically write extractor output JSON."""

    def __init__(self, out_path: str) -> None:
        """
        Initialize an output writer for the given path.

        Args:
            out_path (str): path to the extractor JSON output file.
        """
        self.out_path = Path(out_path)

    def read(self) -> dict:
        """
        Read and validate the current JSON output file.

        Returns:
            dict: parsed JSON object, or an empty dict if the file is missing
            or empty.

        Raises:
            OutputDataError: existing file contents are not valid JSON object
            data and cannot be merged safely.
        """
        try:
            file_text = self.out_path.read_text(encoding="UTF-8")
        except FileNotFoundError:
            return {}

        if not file_text.strip():
            return {}

        try:
            json_data = json.loads(file_text)
        except JSONDecodeError as exc:
            raise OutputDataError(
                f'Output file at "{self.out_path}" does not contain valid JSON.'
            ) from exc

        if not isinstance(json_data, dict):
            raise OutputDataError(
                f'Output file at "{self.out_path}" must contain a JSON object.'
            )

        return json_data

    def merge_and_write(self, output_chunk: dict) -> dict:
        """
        Merge a repo-scoped output chunk into the file and write atomically.

        Args:
            output_chunk (dict): top-level output data to merge.

        Returns:
            dict: merged output dictionary written to disk.
        """
        merged_output = merge_output_chunks(self.read(), output_chunk)
        self._write_atomic(merged_output)

        return merged_output

    def merge_repo_data(self, repo_slug: str, repo_data: dict) -> dict:
        """
        Merge one repository's extracted data into the output file.

        Args:
            repo_slug (str): canonical GitHub repository slug in owner/name form.
            repo_data (dict): extracted data keyed by issue or PR number.

        Returns:
            dict: merged output dictionary written to disk.
        """
        return self.merge_and_write(build_repo_output_chunk(repo_slug, repo_data))

    def _write_atomic(self, out_dict: dict) -> None:
        """
        Atomically write output JSON using a temporary file and os.replace.

        Writing to a sibling temp file prevents partially written JSON from
        corrupting the output path if the process is interrupted mid-write.
        """
        self.out_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="UTF-8",
                dir=self.out_path.parent,
                delete=False,
            ) as tmp_file:
                json.dump(out_dict, tmp_file, ensure_ascii=False, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                temp_path = Path(tmp_file.name)

            os.replace(temp_path, self.out_path)

        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()


def _merge_dicts_recursive(base_dict: dict, add_dict: dict) -> None:
    """
    Recursively merge add_dict into base_dict.

    This merge strategy preserves nested repo and issue dictionaries while
    allowing later writes to replace scalar leaf values when necessary.
    """
    for key, value in add_dict.items():
        if (
            key in base_dict
            and isinstance(base_dict[key], dict)
            and isinstance(value, dict)
        ):
            _merge_dicts_recursive(base_dict[key], value)
        else:
            base_dict[key] = deepcopy(value)
