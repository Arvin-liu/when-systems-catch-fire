import json
from pathlib import Path

from tools.causal_fabric.diff import causal_fabric_diff
from tools.causal_fabric.projector import project_file
from tools.causal_fabric.renderer import render_markdown
from tools.causal_fabric.validator import iter_example_paths, load_fabric, validate_all


def test_all_examples_validate():
    result = validate_all()
    assert result["status"] == "PASS", result
    assert result["checked"] >= 5


def test_projector_and_renderer_are_deterministic():
    path = Path("data/architecture/multiscale-causal-fabric/examples/ai-deployment.json")
    first = project_file(path)
    second = project_file(path)
    assert first == second
    rendered = render_markdown(load_fabric(path))
    assert "not causal proof" in rendered
    assert "mcf-example-ai-deployment" in rendered


def test_diff_detects_relation_class_change_without_truth_upgrade():
    path = Path("data/architecture/multiscale-causal-fabric/examples/quantum-entanglement-negative.json")
    before = load_fabric(path)
    after = json.loads(json.dumps(before))
    after["relations"][0]["relation_class"] = "unknown_relation"
    diff = causal_fabric_diff(before, after)
    assert diff["relation_class_changes"] == [
        {
            "relation_id": "qe-r-correlation",
            "before": "correlation_only",
            "after": "unknown_relation",
        }
    ]


def test_every_example_has_human_readable_companion():
    for path in iter_example_paths():
        assert path.with_suffix(".md").exists()

