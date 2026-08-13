"""T1 and T4: reports are boundary-minted and inert to belief."""

import dataclasses
import inspect
from pathlib import Path

from fixtures_cut3 import D_IN, closure_kwargs, report

import science
from science.admission import admit
from science.closure import build_closure
from science.dataset import ByteObservation, DatasetDeclaration, ResourceDeclaration, admission_state, dataset_address
from science.record import AssessmentValue, RunInput, RunValue
from science.report import ActReport
from science.verification import Verification


def admitted_scenario():
    d = DatasetDeclaration(resources=(ResourceDeclaration(name="r", digest=D_IN),))
    run = RunValue(ref="run-1", spec="spec-1", inputs=(RunInput(role="observes", dataset=d),))
    assessment = AssessmentValue(
        spec="spec-1",
        run="run-1",
        proposition="prop-1",
        outcome="supported",
        interpretation_rule="rule-1",
    )
    observations = {dataset_address(d): (ByteObservation(digest=D_IN, location="repo://data"),)}
    admitting = (Verification(ref="v1", assessment=assessment.identity(), scope="clean-environment", verdict="passed"),)
    return d, run, assessment, observations, admitting


def test_t4_adding_and_removing_reports_leaves_belief_admission_and_eligibility_byte_unchanged():
    d, run, assessment, observations, admitting = admitted_scenario()
    kwargs = closure_kwargs((assessment,), {"run-1": run})
    before_digest = build_closure(**kwargs).digest()
    before_admission = admit(assessment, run, observations, admitting)
    before_state = admission_state(d, observations[dataset_address(d)])
    reports = {r.identity(): r for r in (report(), report(event_token="tok-2"))}
    assert reports  # The reports exist and reference nothing that protects them.
    after_digest = build_closure(**kwargs).digest()
    after_admission = admit(assessment, run, observations, admitting)
    after_state = admission_state(d, observations[dataset_address(d)])
    assert after_digest == before_digest  # Byte-unchanged, not merely equal-valued.
    assert after_admission == before_admission
    assert type(after_state) is type(before_state)
    reports.clear()  # Removal is as inert as addition.
    assert build_closure(**kwargs).digest() == before_digest


def test_t4_no_belief_bearing_signature_names_a_report():
    for fn in (build_closure, admit, admission_state):
        assert not {"report", "reports", "act_report"} & set(inspect.signature(fn).parameters)
    from science.belief import Records

    assert "reports" not in {field.name for field in dataclasses.fields(Records)}


def test_t4_the_belief_modules_never_import_the_report_layer():
    # Inert BY TYPE: the reference conveys neither protection nor force, and
    # the derivations cannot even see the layer (act-report §2.3).
    import science.admission
    import science.belief
    import science.closure
    import science.dataset

    for module in (science.admission, science.belief, science.closure, science.dataset):
        source = inspect.getsource(module)
        assert "science.report" not in source and "science.boundary" not in source


def test_t1_no_construction_path_authors_an_act_report():
    import science.boundary as boundary_module
    import science.report as report_module

    assert "_mint_report" not in report_module.__all__
    report_fields = {field.name for field in dataclasses.fields(ActReport)}
    for module in (report_module, boundary_module):
        for name in module.__all__:
            value = getattr(module, name)
            if callable(value) and not isinstance(value, type):
                params = set(inspect.signature(value).parameters)
                # Boundary operation metadata is not an authored report.
                assert not report_fields <= params, (module.__name__, name)


def test_t1_the_constructor_is_reachable_only_from_the_boundary():
    # The one src caller of the private constructor is the boundary — the
    # in-slice form of "minted only by the boundary" (cut 3 §9 item 2).
    src = Path(science.__file__).parent
    callers = [path.name for path in src.rglob("*.py") if "_mint_report" in path.read_text(encoding="utf-8")]
    assert sorted(callers) == ["boundary.py", "report.py"]
