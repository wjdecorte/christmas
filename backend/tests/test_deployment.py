"""Deployment contracts prevent accidental source builds or release publication drift."""

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_nas_files_match_and_only_pull():
    root = (ROOT / "compose.yaml").read_text()
    assert root == (ROOT / "deploy/synology/compose.yaml").read_text()
    service = yaml.safe_load(root)["services"]["app"]
    assert "build" not in service
    assert service["image"] == "${CHRISTMAS_IMAGE:-ghcr.io/wjdecorte/christmas:latest}"
    assert service["read_only"] is True
    assert service["restart"] == "unless-stopped"
    assert service["healthcheck"]["test"][0] == "CMD"
    assert "/data" in service["volumes"][0]
    assert (ROOT / ".env.example").read_text() == (
        ROOT / "deploy/synology/.env.example"
    ).read_text()
    override = yaml.safe_load((ROOT / "compose.build.yaml").read_text())["services"][
        "app"
    ]
    assert override["build"] == "."
    assert override["image"] == "north-georgia-holiday-events:local"


def test_ci_checks_gate_both_architectures_and_publishing():
    workflow = yaml.safe_load((ROOT / ".github/workflows/image.yaml").read_text())
    jobs = workflow["jobs"]
    assert jobs["build"]["needs"] == "verify"
    assert jobs["publish"]["needs"] == "build"
    assert jobs["build"]["if"] == "github.event_name != 'pull_request'"
    architectures = {
        item["arch"] for item in jobs["build"]["strategy"]["matrix"]["include"]
    }
    assert architectures == {"amd64", "arm64"}
    verify = "\n".join(step.get("run", "") for step in jobs["verify"]["steps"])
    assert (
        "pytest -q" in verify
        and "frontend test" in verify
        and "frontend run build" in verify
    )
    publish = "\n".join(step.get("run", "") for step in jobs["publish"]["steps"])
    assert 'contains(["amd64", "arm64"])' in publish
    assert "packages" not in workflow["permissions"]
    assert jobs["publish"]["permissions"]["packages"] == "write"
