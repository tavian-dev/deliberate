"""Tests for campaign lifecycle (Class C full pipeline)."""

import tempfile
from pathlib import Path

import pytest
from deliberate import WeightClass
from deliberate.process import (
    create_campaign, campaign_status, campaign_step,
    CAMPAIGN_STEPS,
)
from deliberate.enforce import check_prerequisites


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestCreateCampaign:
    def test_creates_directory(self, tmp_dir):
        campaign = create_campaign("redesign-auth", "Redesign authentication", tmp_dir)
        assert (tmp_dir / "redesign-auth").is_dir()

    def test_returns_campaign_dict(self, tmp_dir):
        campaign = create_campaign("my-feature", "Build a thing", tmp_dir)
        assert campaign["name"] == "my-feature"
        assert campaign["status"] == "created"
        assert campaign["weight_class"] == "campaign"

    def test_creates_status_file(self, tmp_dir):
        create_campaign("test-feat", "Test", tmp_dir)
        assert (tmp_dir / "test-feat" / "status.json").exists()


class TestCampaignStep:
    def test_spec_creates_file(self, tmp_dir):
        create_campaign("feat", "Feature", tmp_dir)
        campaign_dir = tmp_dir / "feat"
        result = campaign_step(campaign_dir, "spec", "Requirements go here")
        assert (campaign_dir / "spec.md").exists()
        assert "Requirements go here" in (campaign_dir / "spec.md").read_text()

    def test_plan_requires_spec(self, tmp_dir):
        create_campaign("feat", "Feature", tmp_dir)
        campaign_dir = tmp_dir / "feat"
        with pytest.raises(ValueError, match="spec.md"):
            campaign_step(campaign_dir, "plan", "Plan content")

    def test_plan_works_after_spec(self, tmp_dir):
        create_campaign("feat", "Feature", tmp_dir)
        campaign_dir = tmp_dir / "feat"
        campaign_step(campaign_dir, "spec", "Spec content")
        campaign_step(campaign_dir, "plan", "Plan content")
        assert (campaign_dir / "plan.md").exists()

    def test_tasks_requires_plan(self, tmp_dir):
        create_campaign("feat", "Feature", tmp_dir)
        campaign_dir = tmp_dir / "feat"
        campaign_step(campaign_dir, "spec", "Spec")
        with pytest.raises(ValueError, match="plan.md"):
            campaign_step(campaign_dir, "tasks", "Tasks content")

    def test_full_pipeline(self, tmp_dir):
        create_campaign("feat", "Feature", tmp_dir)
        d = tmp_dir / "feat"
        campaign_step(d, "spec", "Spec content")
        campaign_step(d, "plan", "Plan content")
        campaign_step(d, "tasks", "Tasks content")
        assert (d / "spec.md").exists()
        assert (d / "plan.md").exists()
        assert (d / "tasks.md").exists()

    def test_status_updates_on_each_step(self, tmp_dir):
        create_campaign("feat", "Feature", tmp_dir)
        d = tmp_dir / "feat"
        assert campaign_status(d)["status"] == "created"
        campaign_step(d, "spec", "S")
        assert campaign_status(d)["status"] == "specifying"
        campaign_step(d, "plan", "P")
        assert campaign_status(d)["status"] == "planning"
        campaign_step(d, "tasks", "T")
        assert campaign_status(d)["status"] == "tasking"


class TestCampaignStatus:
    def test_no_campaign(self, tmp_dir):
        status = campaign_status(tmp_dir / "nonexistent")
        assert status["status"] == "none"

    def test_new_campaign(self, tmp_dir):
        create_campaign("feat", "Feature", tmp_dir)
        status = campaign_status(tmp_dir / "feat")
        assert status["status"] == "created"
        assert status["name"] == "feat"
        assert status["artifacts"]["spec"] is False
        assert status["artifacts"]["plan"] is False
        assert status["artifacts"]["tasks"] is False

    def test_artifacts_tracked(self, tmp_dir):
        create_campaign("feat", "Feature", tmp_dir)
        d = tmp_dir / "feat"
        campaign_step(d, "spec", "Content")
        status = campaign_status(d)
        assert status["artifacts"]["spec"] is True
        assert status["artifacts"]["plan"] is False


class TestCampaignSteps:
    def test_step_order(self):
        assert CAMPAIGN_STEPS == ["spec", "plan", "tasks"]
