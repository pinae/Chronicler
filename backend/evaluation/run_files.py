"""Finding a story's run files (written by `manage.py replay`, docs/run-file-format.md)."""

from pathlib import Path


class NoRunFile(Exception):
    pass


def latest_run_file(runs_dir: Path, story: str) -> Path:
    """Run files are named by their UTC timestamp, so the last name is the latest run."""
    run_files = sorted((runs_dir / story).glob("*.json"))
    if not run_files:
        raise NoRunFile(f"no run file for {story}; run `manage.py replay {story}` first")
    return run_files[-1]
