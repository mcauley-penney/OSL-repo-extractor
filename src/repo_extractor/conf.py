"""The conf module exposes the Cfg class."""

from copy import deepcopy
import sys
from typing import Iterator

import cerberus


def _dedupe_keep_order(items: list[str]) -> list[str]:
    """Return a list with duplicate string entries removed in-order."""
    return [*dict.fromkeys(items)]


class Cfg:
    """Validated and normalized configuration for batch extraction runs."""

    def __init__(self, cfg_dict: dict, cfg_schema: dict) -> None:
        """
        Initialize an object to hold validated runtime configuration.

        Args:
            cfg_dict (dict): configuration values provided by the user.
            cfg_schema (dict): Cerberus schema used to validate cfg_dict.
        """
        self.raw_cfg_dict = deepcopy(cfg_dict)
        self.cfg_schema = cfg_schema

        self.__validate_dict_entries()
        self.cfg_dict = self.__normalize_cfg_dict(self.raw_cfg_dict)

    def get_cfg_val(self, key: str):
        """
        Return the value mapped to the given top-level runtime key.

        Args:
            key (str): associated key for desired value.

        Returns:
            list|dict|str: value in the top level of the normalized config.
        """
        return self.cfg_dict[key]

    def set_cfg_val(self, key: str, val) -> None:
        """
        Set a value inside of the normalized configuration dictionary.

        Args:
            key (str): the key of the dict entry to modify.
            val (): value to assign to dict[key].
        """
        self.cfg_dict[key] = val

    def get_targets(self) -> list[dict]:
        """Return the normalized per-target runtime configurations."""
        return self.cfg_dict["targets"]

    def get_target_cfg(self, index: int) -> dict:
        """Return a single normalized target configuration by index."""
        return self.get_targets()[index]

    def iter_targets(self) -> Iterator[dict]:
        """Iterate through normalized per-target runtime configurations."""
        yield from self.get_targets()

    def as_dict(self) -> dict:
        """Return the normalized runtime configuration dictionary."""
        return self.cfg_dict

    def __validate_dict_entries(self) -> None:
        """
        Validate the given configuration against the provided schema.

        Use Cerberus to check all entries in the configuration dictionary
        for correctness of type and content. Fail-stop behavior is used if
        the configuration does not meet schema specification.
        """
        validator = cerberus.Validator(self.cfg_schema, require_all=False)

        if not validator.validate(document=self.raw_cfg_dict):
            print(f"Validation error!\n{validator.errors}")
            sys.exit(1)

    def __normalize_cfg_dict(self, cfg_dict: dict) -> dict:
        """
        Normalize a validated batch configuration into runtime form.

        The runtime form keeps the batch-level auth and output settings at the
        top level and expands defaults into each target so downstream code can
        consume a concrete list of extractor jobs.
        """
        defaults = cfg_dict["defaults"]
        auth_path = cfg_dict["auth_path"]
        output_path = cfg_dict["output_path"]

        normalized_targets = [
            self.__normalize_target_cfg(
                target_cfg,
                defaults,
                auth_path,
                output_path,
            )
            for target_cfg in cfg_dict["targets"]
        ]

        return {
            "auth_path": auth_path,
            "output_path": output_path,
            "targets": normalized_targets,
        }

    def __normalize_target_cfg(
        self,
        target_cfg: dict,
        defaults: dict,
        auth_path: str,
        output_path: str,
    ) -> dict:
        """Normalize one target by merging target-level overrides over defaults."""
        fields_cfg = self.__merge_fields(
            defaults["fields"],
            target_cfg.get("fields"),
        )

        return {
            "auth_path": auth_path,
            "output_path": output_path,
            "repo": target_cfg["repo"],
            "range": self.__normalize_range(target_cfg["range"]),
            "state": target_cfg.get("state", defaults["state"]),
            "labels": self.__normalize_string_list(
                target_cfg.get("labels", defaults["labels"])
            ),
            **fields_cfg,
        }

    @staticmethod
    def __merge_fields(default_fields: dict, override_fields: dict | None) -> dict:
        """
        Merge default field selectors with an optional target-level override.

        Each extractor item type is merged independently so a target may
        override only the issue, comment, or commit fields it needs to change.
        """
        override_fields = override_fields or {}

        return {
            "issues": Cfg.__normalize_string_list(
                override_fields.get("issues", default_fields["issues"])
            ),
            "comments": Cfg.__normalize_string_list(
                override_fields.get("comments", default_fields["comments"])
            ),
            "commits": Cfg.__normalize_string_list(
                override_fields.get("commits", default_fields["commits"])
            ),
        }

    @staticmethod
    def __normalize_range(range_cfg: dict) -> dict:
        """
        Normalize a target range object.

        The schema ensures that start is present and valid. Normalization makes
        the optional end key explicit so downstream code can rely on it.
        """
        return {
            "start": range_cfg["start"],
            "end": range_cfg.get("end"),
        }

    @staticmethod
    def __normalize_string_list(items: list[str]) -> list[str]:
        """Copy and deduplicate a list of strings while preserving order."""
        return _dedupe_keep_order([*items])
