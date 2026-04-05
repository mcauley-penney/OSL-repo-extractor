"""Batch orchestration tools for repository extraction."""

from __future__ import annotations

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

            print(f"\nRunning target {index}/{total_targets}: {repo_slug}")
            print(
                f"{TAB}Requested range: "
                f'{self.__format_range(target_cfg["range"])}'
            )

            repo_data = self.__run_target(target_cfg)
            repo_chunk = output.build_repo_output_chunk(repo_slug, repo_data)
            combined_output = output.merge_output_chunks(combined_output, repo_chunk)

        return combined_output

    def __run_target(self, target_cfg: dict) -> dict:
        """
        Run extraction for one normalized target configuration.

        Args:
            target_cfg (dict): normalized target configuration.

        Returns:
            dict: repo-local output keyed by issue or PR number.

        Raises:
            RunnerError: extraction or output persistence failed.
        """
        repo_slug = target_cfg["repo"]

        try:
            repo_extractor = extractor.Extractor(
                target_cfg,
                gh_sesh=self.gh_sesh,
                flush_callback=self.__flush_repo_chunk,
            )
            repo_data = repo_extractor.extract_repo_data()
        except KeyboardInterrupt as exc:
            raise RunnerError(
                f'Extraction interrupted while processing "{repo_slug}".'
            ) from exc
        except (
            extractor.ExtractorError,
            extractor.GithubSessionError,
            output.OutputDataError,
        ) as exc:
            raise RunnerError(
                f'Extraction failed while processing "{repo_slug}".'
            ) from exc

        return repo_data

    def __flush_repo_chunk(self, repo_slug: str, repo_data_chunk: dict) -> None:
        """
        Persist a partial repo-local output chunk to the configured writer.

        Args:
            repo_slug (str): canonical GitHub repo slug.
            repo_data_chunk (dict): repo-local issue or PR data to merge.
        """
        self.output_writer.merge_repo_data(repo_slug, repo_data_chunk)

    @staticmethod
    def __format_range(range_cfg: dict) -> str:
        """
        Format a target range for user-facing progress output.

        Args:
            range_cfg (dict): normalized target range.

        Returns:
            str: printable range string.
        """
        end_text = "latest" if range_cfg["end"] is None else f'#{range_cfg["end"]}'

        return f'#{range_cfg["start"]} to {end_text}'


def run_batch(cfg_obj: conf.Cfg) -> dict:
    """
    Run a batch extraction using the provided normalized configuration.

    Args:
        cfg_obj (conf.Cfg): validated and normalized batch configuration.

    Returns:
        dict: combined repo-keyed extraction output.
    """
    return BatchRunner(cfg_obj).run()
