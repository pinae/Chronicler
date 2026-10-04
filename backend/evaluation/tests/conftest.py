import shutil

import pytest
import yaml

STEWARD_GROUND_TRUTH = {
    "reveal_t": 22,
    "true_hypothesis": {"schema": "betrayal", "binding": {"T": "aldric", "V": "mira"}},
    "dormant_window": [8, 21],
}


@pytest.fixture
def steward_with_ground_truth(tmp_path, settings):
    """Stories are read from a copy holding steward with a ground truth; returns a runs directory."""
    stories_dir = tmp_path / "stories"
    shutil.copytree(settings.FIXTURE_STORIES_DIR / "steward", stories_dir / "steward")
    shutil.copytree(settings.FIXTURE_STORIES_DIR / "minimal", stories_dir / "minimal")
    (stories_dir / "steward" / "ground_truth.yaml").write_text(yaml.safe_dump(STEWARD_GROUND_TRUTH))
    settings.FIXTURE_STORIES_DIR = stories_dir
    return tmp_path / "runs"
