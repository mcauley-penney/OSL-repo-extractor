"""Batch orchestration tools for repository extraction."""

from __future__ import annotations

from copy import deepcopy
import json

from repo_extractor import conf, extractor, output

TAB = " " * 4


class RunnerError(RuntimeError):
    """Raised when a batch extraction run cannot complete successfully."""


class BatchRunner:
    """Coordinate batch extraction across multiple normalized repo targets."""

    def __init__(
        self,
        cfg_obj: conf.Cfg,
        gh_sesh: extractor.GithubSession | None = None,
        output_writer: output.OutputWriter | None = None,
    ) -> None:
        """
        Initialize a batch runner for the given normalized configuration.

        Args:
            cfg_obj (conf.Cfg): validated and normalized batch configuration.
            gh_sesh (GithubSession | None): optional shared GitHub session.
            output_writer (OutputWriter | None): optional output writer.
        """
        self.cfg = cfg_obj
        self.gh_sesh = gh_sesh or extractor.GithubSession(
            self.cfg.get_cfg_val("auth_path")
        )
        self.output_writer = output_writer or output.OutputWriter(
            self.cfg.get_cfg_val("output_path")
        )
        self.report_writer = output.OutputWriter(self.cfg.get_cfg_val("report_path"))
        self.report = {"repositories": {}}

    def run(self) -> dict:
        """
        Run extraction for every configured target and return combined results.

        Returns:
            dict: combined output keyed by repository slug.

        Raises:
            RunnerError: extraction or output writing failed.
        """
        combined_output: dict = {}
        targets = self.cfg.get_targets()
        total_targets = len(targets)

        for index, target_cfg in enumerate(targets, start=1):
            repo_slug = target_cfg["repo"]
            self.__ensure_repo_report(repo_slug)

            print(f"\nRunning target {index}/{total_targets}: {repo_slug}")
            print(f"{TAB}Requested ranges: {self.__format_ranges(target_cfg['range'])}")

            repo_data = self.__run_target(target_cfg)
            if repo_data is None:
                continue

            repo_chunk = output.build_repo_output_chunk(repo_slug, repo_data)
            combined_output = output.merge_output_chunks(combined_output, repo_chunk)

        self.report_writer.write_document(self.report)
        self.print_report()
        return combined_output

    def get_report(self) -> dict:
        """Return a copy of the report compiled during the batch run."""
        return deepcopy(self.report)

    def print_report(self) -> None:
        """Print the persisted report as formatted JSON."""
        print("\nExtraction report")
        print(json.dumps(self.report, indent=2))

    def __run_target(self, target_cfg: dict) -> dict | None:
        """
        Run extraction for one normalized target configuration.

        Args:
            target_cfg (dict): normalized target configuration.

        Returns:
            dict | None: repo-local output keyed by issue or PR number. None
                means the repository was unavailable and was skipped.

        Raises:
            RunnerError: extraction or output persistence failed.
        """
        repo_slug = target_cfg["repo"]

        try:
            repo_extractor = extractor.Extractor(
                target_cfg,
                gh_sesh=self.gh_sesh,
                flush_callback=self.__flush_repo_chunk,
                item_result_callback=self.__record_item_result,
            )
            repo_data = repo_extractor.extract_repo_data()
            self.__ensure_repo_report(repo_slug)["status"] = "completed"
        except KeyboardInterrupt as exc:
            raise RunnerError(
                f'Extraction interrupted while processing "{repo_slug}".'
            ) from exc
        except extractor.ExtractorError as exc:
            repo_report = self.__ensure_repo_report(repo_slug)
            repo_report["status"] = "failed"
            repo_report["error"] = {"message": str(exc)}
            print(f"{TAB}Skipping repository {repo_slug}: {exc}")
            return None
        except (
            extractor.GithubSessionError,
            output.OutputDataError,
        ) as exc:
            raise RunnerError(
                f'Extraction failed while processing "{repo_slug}".'
            ) from exc

        return repo_data

    def __ensure_repo_report(self, repo_slug: str) -> dict:
        """Create or return the report entry for a repository."""
        return self.report["repositories"].setdefault(
            repo_slug,
            {
                "status": "running",
                "extracted_items": [],
                "skipped_items": [],
            },
        )

    def __record_item_result(
        self,
        repo_slug: str,
        item_number: int,
        extracted: bool,
        is_pr: bool | None,
        error: dict | None,
    ) -> None:
        """Record one successfully extracted or skipped issue/PR."""
        repo_report = self.__ensure_repo_report(repo_slug)

        if extracted:
            repo_report["extracted_items"].append(item_number)
        else:
            repo_report["skipped_items"].append(
                {
                    "number": item_number,
                    "is_pr": is_pr,
                    "error": (
                        deepcopy(error)
                        if error is not None
                        else {"message": "unknown error"}
                    ),
                }
            )

    def __flush_repo_chunk(self, repo_slug: str, repo_data_chunk: dict) -> None:
        """
        Persist a partial repo-local output chunk to the configured writer.

        Args:
            repo_slug (str): canonical GitHub repo slug.
            repo_data_chunk (dict): repo-local issue or PR data to merge.
        """
        self.output_writer.merge_repo_data(repo_slug, repo_data_chunk)

    @staticmethod
    def __format_ranges(range_cfg: list) -> str:
        """
        Format target issue selectors for user-facing progress output.

        Args:
            range_cfg (list): normalized target issue selectors.

        Returns:
            str: printable range string.
        """
        formatted = []
        for selector in range_cfg:
            if isinstance(selector, int):
                formatted.append(f"#{selector}")
                continue

            start, end = selector
            end_text = "latest" if end == -1 else f"#{end}"
            formatted.append(f"#{start} to {end_text}")

        return ", ".join(formatted)


def run_batch(cfg_obj: conf.Cfg) -> dict:
    """
    Run a batch extraction using the provided normalized configuration.

    Args:
        cfg_obj (conf.Cfg): validated and normalized batch configuration.

    Returns:
        dict: combined repo-keyed extraction output.
    """
    return BatchRunner(cfg_obj).run()
