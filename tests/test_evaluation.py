from evaluation.compare_models import mechanism_jaccard, mechanism_names
from evaluation.run_smoke import load_examples
from evaluation.summarize_results import controlled_mutation_passes, percentile, render_markdown, summarize
from evaluation.run_teacher_audit import TeacherAuditResponse, audit_issues
from evaluation.summarize_teacher_audit import audit_passes, summarize_audits
from evaluation.validate_dataset import validate_examples


def record(*mechanisms: str) -> dict:
    return {
        "status": "ok",
        "result": {"mechanisms": [{"mechanism": mechanism} for mechanism in mechanisms]},
    }


def test_mechanism_names_ignores_failed_records() -> None:
    assert mechanism_names({"status": "error"}) == set()


def test_mechanism_jaccard() -> None:
    left = record("misdirection", "irony")
    right = record("misdirection", "incongruity")
    assert mechanism_jaccard(left, right) == 1 / 3


def test_mechanism_jaccard_is_none_for_two_empty_results() -> None:
    assert mechanism_jaccard(record(), record()) is None


def full_flow_record(*, changed_only_target_gene: bool = True) -> dict:
    return {
        "id": "example-1",
        "model": "gemma4:e2b",
        "target_gene": "brevity",
        "source": "original",
        "license": "CC0-1.0",
        "status": "ok",
        "latency_seconds": 12.0,
        "result": {
            "mutation": {
                "source_text": "This setup is deliberately a little too long for the punchline.",
                "target_gene": "brevity",
                "variants": [
                    {
                        "label": "A",
                        "text": "This setup is too long for the punchline.",
                        "changed_gene": "brevity",
                        "changed_only_target_gene": changed_only_target_gene,
                    },
                    {
                        "label": "B",
                        "text": "The setup runs long for its punchline.",
                        "changed_gene": "brevity",
                        "changed_only_target_gene": True,
                    },
                ],
            },
            "stage_latency_seconds": {"analyze": 5.0, "mutate": 4.0, "compare": 3.0},
        },
    }


def test_percentile_uses_nearest_rank() -> None:
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.95) == 4.0


def test_controlled_mutation_checks_self_report_and_brevity() -> None:
    assert controlled_mutation_passes(full_flow_record()) is True
    assert controlled_mutation_passes(full_flow_record(changed_only_target_gene=False)) is False


def test_summarize_produces_writeup_metrics() -> None:
    result = summarize([full_flow_record(), {"model": "gemma4:e2b", "status": "error", "error": "timeout"}])
    metrics = result["by_model"]["gemma4:e2b"]

    assert metrics["success_rate"] == 0.5
    assert metrics["controlled_mutation_pass_rate"] == 1.0
    assert metrics["latency_seconds"]["p50"] == 12.0
    assert metrics["licensed_record_rate"] == 0.5
    assert "Controlled mutation" in render_markdown(result)


def test_load_examples_can_select_ids(tmp_path) -> None:
    path = tmp_path / "examples.jsonl"
    path.write_text('{"id":"a"}\n{"id":"b"}\n', encoding="utf-8")

    assert load_examples(path, limit=None, ids=["b"]) == [{"id": "b"}]


def test_dataset_validator_accepts_complete_unique_rows(tmp_path) -> None:
    path = tmp_path / "examples.jsonl"
    path.write_text(
        '{"id":"short_joke_001","text":"A sufficiently long original joke.",'
        '"source":"project-original-ai-assisted","license":"CC0-1.0","split":"seed",'
        '"calibration_status":"calibrated","target_gene":"brevity",'
        '"expected_mechanisms":["irony"]}\n',
        encoding="utf-8",
    )

    report = validate_examples(path)
    assert report["status"] == "ok"
    assert report["examples"] == 1


def test_dataset_validator_rejects_duplicate_rows_and_unvalidated_gene(tmp_path) -> None:
    path = tmp_path / "examples.jsonl"
    row = (
        '{"id":"short_joke_001","text":"A sufficiently long original joke.",'
        '"source":"project-original-ai-assisted","license":"CC0-1.0","split":"seed",'
        '"calibration_status":"calibrated","target_gene":"specificity",'
        '"expected_mechanisms":["irony"]}'
    )
    path.write_text(f"{row}\n{row}\n", encoding="utf-8")

    report = validate_examples(path, minimum_examples=3)
    assert report["status"] == "error"
    assert any("duplicate ids" in error for error in report["errors"])
    assert any("not a calibrated gene" in error for error in report["errors"])
    assert any("minimum is 3" in error for error in report["errors"])


def teacher_audit(label: str, isolated: bool = True) -> dict:
    return {
        "label": label,
        "target_gene_isolated": isolated,
        "premise_preserved": True,
        "non_target_mechanisms_preserved": True,
        "meaningful_edit": True,
        "failure_modes": [] if isolated else ["target gene drift"],
        "rationale": "The requested dimension changed while the premise remained stable.",
        "confidence": 0.8,
    }


def test_teacher_audit_requires_exact_variant_labels() -> None:
    response = TeacherAuditResponse(
        audits=[teacher_audit("A"), teacher_audit("A")],
        overall_assessment="One duplicate label.",
        limitations=["Model-based diagnostic."],
    )
    assert audit_issues([{"label": "A"}, {"label": "B"}], response)


def test_teacher_summary_reports_full_rubric_pass_rate() -> None:
    records = [
        {
            "status": "ok",
            "target_gene": "brevity",
            "latency_seconds": 10.0,
            "audit": {"audits": [teacher_audit("A"), teacher_audit("B", isolated=False)]},
        }
    ]
    summary = summarize_audits(records)

    assert audit_passes(records[0]["audit"]["audits"][0]) is True
    assert summary["variant_pass_rate"] == 0.5
    assert summary["target_gene_isolation_rate"] == 0.5
    assert summary["by_candidate_method"]["unknown"]["variant_pass_rate"] == 0.5
    assert summary["by_candidate_method"]["unknown"]["record_completion_rate"] == 1.0
