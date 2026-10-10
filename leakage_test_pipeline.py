"""pytest: generate -> pipeline on a temp dir; recall >= 90% and nothing auto-sent."""
import pytest

import leakage_generate
import leakage_pipeline
import leakage_report


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    d = tmp_path_factory.mktemp("leakage")
    leakage_generate.main(d)
    res = leakage_pipeline.run(d)
    res["dir"] = d
    return res


def test_recall_per_leak_type_and_overall(result):
    det = result["metrics"]["detection"]
    for t, v in det.items():
        assert v["recall"] >= 0.90, (t, v)
    assert det["ALL"]["recall"] >= 0.90


def test_five_leak_types_present(result):
    assert len({l["type"] for l in result["leaks"]}) == 5


def test_no_action_is_sent(result):
    assert result["actions"] and len(result["actions"]) == len(result["leaks"])
    assert all(a["status"] == "awaiting approval" for a in result["actions"])
    assert not any(a["status"] == "sent" for a in result["actions"])


def test_matching_precision_reasonable(result):
    assert result["metrics"]["matching"]["combined"]["precision"] >= 0.95


def test_report_renders(result):
    out = leakage_report.render(result["dir"])
    txt = out.read_text()
    assert "at risk" in txt and "Synthetic data" in txt
