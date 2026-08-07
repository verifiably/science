"""N2 — every oracle row can fail, applied to cut 1's own selected arms.

The harness runs each declared arm twice: once unsabotaged, where its checks must
**pass**, and once with its sabotage applied, where they must **fail**. Both
directions are needed and neither is decoration.

* Without the first, a check that can never pass looks like a sound arm. So does
  a **typo'd node id** — `pytest` exits non-zero for a usage error, and a harness
  reading only the exit code would score a name that resolves to nothing as the
  healthiest arm in the table.
* Without the second, the arm asserts nothing about the property it names.

A sabotage is applied to a **copy** of the package, and the arm's checks run in a
subprocess against it. Nothing writes to the working tree, which is what makes it
safe to run these concurrently and safe to interrupt — the hand-run matrices this
replaces mutated files in place and restored them in a `finally`, one `SIGINT`
away from leaving a sabotaged source on disk.

**Three findings, not two.** An arm can be `sound`, `vacuous` — its checks passed
under its own sabotage — or `stale`, where the sabotage no longer matches the
code it was written against. Staleness happened twice during this build, and a
stale sabotage is indistinguishable from a passing arm unless it is looked for:
the mutation silently does nothing, the checks pass, and the harness reports the
arm healthy. It is malformed contract content in the same way vacuity is, so it
is reported the same way.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import pytest
from n2_arms import ARMS, STALE_BY_CONSTRUCTION, VACUOUS_BY_CONSTRUCTION, Arm, Sabotage

PACKAGE = Path(__file__).resolve().parent.parent / "src" / "science"
TESTS = Path(__file__).resolve().parent


class MalformedArm(Exception):
    """An arm that does not do what an arm is for.

    N2's second clause: *construct a row whose check passes under sabotage and
    assert the row itself is reported as malformed contract content*. This is
    that report. It is deliberately not an assertion failure inside some test —
    the finding is about the **contract content**, not about the code under test,
    and a suite that could only say *"a test failed"* would file a defective row
    and a real regression under one heading.
    """


@dataclass(frozen=True)
class Finding:
    arm: Arm
    verdict: str
    """`sound`, `vacuous`, or `stale`."""

    detail: str = ""


def _run_checks(arm: Arm, package: Path | None) -> subprocess.CompletedProcess[str]:
    """Run this arm's checks, optionally against a sabotaged copy of the package."""
    env = {"PATH": "/usr/bin:/bin", "HOME": str(Path.home())}
    if package is not None:
        env["PYTHONPATH"] = str(package.parent)
    # Node ids are declared relative to `tests/` and resolved to absolute paths
    # here, so an arm reads as the suite writes it and neither depends on where
    # the harness happened to be invoked from.
    if not arm.checks:
        # `pytest` with no node ids collects `testpaths`, which includes **this
        # file**, whose arms each invoke `pytest` again. One arm with an empty
        # check list is therefore not a weak arm but a fork bomb, so the refusal
        # lives here as well as in `audit` — the upstream guard states the rule,
        # and this makes breaking it unspellable rather than merely wrong.
        raise MalformedArm("an arm names no check; running pytest with no node ids would collect this file")
    checks = [f"{TESTS}/{check}" for check in arm.checks]
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider", *checks],
        cwd=TESTS.parent,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _sabotage(arm: Arm, into: Path) -> Path | None:
    """Copy the package into `into` and apply the arm's mutation. `None` if it does not apply."""
    package = into / "science"
    shutil.copytree(PACKAGE, package)
    target = package / arm.sabotage.module
    source = target.read_text(encoding="utf-8")
    if source.count(arm.sabotage.before) != 1:
        return None
    target.write_text(source.replace(arm.sabotage.before, arm.sabotage.after), encoding="utf-8")
    return package


def baseline(arm: Arm) -> Finding:
    """The other direction, and it is not a formality.

    A node id that no longer resolves makes `pytest` exit **4** for a usage
    error. Read as an exit code that is indistinguishable from a check that
    failed — so a renamed test would leave its arm scoring `sound` forever while
    asserting nothing at all, and the arm most certain to look healthy would be
    the one that had stopped existing.
    """
    result = _run_checks(arm, package=None)
    if result.returncode != 0:
        return Finding(arm, "unresolved", result.stdout[-4000:])
    return Finding(arm, "resolved")


def audit(arm: Arm, workspace: Path) -> Finding:
    """One arm, one verdict."""
    if not arm.checks:
        # Refused here rather than asserted over the table, because the table
        # assertion is not sabotageable: weakening `assert all(arm.checks ...)`
        # to `assert True` proves only that a deleted test does not run. An arm
        # naming no check would also run `pytest` with no node ids, collect the
        # whole suite, and score by whether *anything* was red.
        return Finding(arm, "stale", "an arm that names no check asserts nothing about the property it names")
    package = _sabotage(arm, workspace)
    if package is None:
        return Finding(
            arm,
            "stale",
            f"the sabotage does not apply to {arm.sabotage.module} exactly once — it was written against "
            "code that has since changed, and a mutation that does nothing scores as a passing arm",
        )
    result = _run_checks(arm, package)
    if result.returncode == 0:
        return Finding(
            arm,
            "vacuous",
            "every check passed with the sabotage applied, so the arm does not assert the property it names",
        )
    return Finding(arm, "sound")


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple[Finding, ...]:
    """Every declared arm, audited once. Concurrent — each arm owns its own copy."""
    root = tmp_path_factory.mktemp("n2")
    with ThreadPoolExecutor(max_workers=8) as pool:
        return tuple(pool.map(lambda pair: audit(pair[1], root / f"arm{pair[0]}"), enumerate(ARMS)))


class TestEveryArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        vacuous = [f for f in findings if f.verdict == "vacuous"]
        if vacuous:
            raise MalformedArm(
                "these arms pass under their own sabotage, which makes them malformed contract content "
                "rather than failing tests:\n" + "\n".join(f"  {f.arm.label}\n    {f.detail}" for f in vacuous)
            )

    def test_no_sabotage_has_gone_stale(self, findings):
        stale = [f for f in findings if f.verdict == "stale"]
        if stale:
            raise MalformedArm(
                "these sabotages no longer match the code they were written against:\n"
                + "\n".join(f"  {f.arm.label}\n    {f.detail}" for f in stale)
            )

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared check resolves and passes against the real package",
            sabotage=ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


class TestTheHarnessCanSeeAVacuousArm:
    """N2's second clause, and the reason this file is not just a test runner.

    *Construct a row whose check passes under sabotage, and assert the row itself
    is reported as malformed contract content.* The arm below is defective by
    construction in the exact way the seven vacuous tests found by hand were: the
    sabotage is a real defect, the check is a real check, and they are about
    different things. If the harness scores it `sound`, the harness cannot see
    the thing it exists to see, and every `sound` above means nothing.
    """

    def test_a_row_that_passes_under_its_own_sabotage_is_reported(self, tmp_path):
        finding = audit(VACUOUS_BY_CONSTRUCTION, tmp_path / "vacuous")
        assert finding.verdict == "vacuous", finding.detail

    def test_the_report_is_malformed_contract_content_not_a_failing_test(self, tmp_path):
        finding = audit(VACUOUS_BY_CONSTRUCTION, tmp_path / "vacuous")
        with pytest.raises(MalformedArm, match="malformed contract content"):
            TestEveryArmAssertsSomething().test_no_arm_survives_its_own_sabotage((finding,))

    def test_its_sabotage_is_a_real_defect_and_its_check_a_real_check(self, tmp_path):
        # Otherwise the demonstration is hollow: an arm can also "pass under
        # sabotage" because the sabotage does nothing, and that is staleness, a
        # different finding. This one mutates real code and the check really runs.
        package = _sabotage(VACUOUS_BY_CONSTRUCTION, tmp_path / "real")
        assert package is not None
        covering = Arm(
            row="N2",
            asserts="the check this arm should have named",
            sabotage=VACUOUS_BY_CONSTRUCTION.sabotage,
            checks=(
                "test_decode.py::TestDecodeInvertsTheProjection::test_every_frozen_row_decodes_back_to_its_own_identity",
            ),
        )
        assert _run_checks(covering, package).returncode != 0


class TestTheArmTableCoversTheCut:
    """The table is contract content, so its shape is asserted rather than assumed."""

    SELECTED = frozenset({"M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11", "M13", "D3"})

    def test_every_row_cut_1_selects_has_at_least_one_arm(self):
        # N2 itself is the eleventh selected row and is not in this set: its arm
        # is this file, and an entry claiming to sabotage it would be circular.
        assert {arm.row for arm in ARMS} == self.SELECTED

    def test_no_arm_claims_a_row_the_cut_defers(self):
        deferred = {"M1", "M2", "M3", "M12", "D4", "D6", "G3", "G7", "S2", "S3", "S8"}
        assert not {arm.row for arm in ARMS} & deferred

    def test_every_arm_names_at_least_one_check(self):
        assert all(arm.checks for arm in ARMS)

    def test_an_arm_naming_no_check_is_refused_by_the_harness(self, tmp_path):
        empty = Arm(row="N2", asserts="an arm with nothing to check", sabotage=ARMS[0].sabotage, checks=())
        assert audit(empty, tmp_path / "empty").verdict == "stale"

    def test_the_runner_refuses_one_too_and_that_is_not_redundant(self):
        # `audit` states the rule; the runner makes breaking it unspellable. Both
        # are needed and each is what makes the other testable: with only the
        # runner's guard an empty arm would raise instead of being reported, and
        # with only the auditor's, any other caller reaching the runner would
        # collect this file and re-enter it — which is a fork bomb, not a slow
        # test. That is not hypothetical: it is what the first version of this
        # harness's own sabotage script did.
        empty = Arm(row="N2", asserts="an arm with nothing to check", sabotage=ARMS[0].sabotage, checks=())
        with pytest.raises(MalformedArm, match="collect this file"):
            _run_checks(empty, package=None)


class TestTheHarnessCanSeeAStaleArm:
    """The finding that vacuity alone does not cover.

    A vacuous arm is written wrong; a stale one **becomes** wrong, when the code
    moves under a table nobody re-reads. Both produce the same false report — the
    checks pass and the arm scores healthy — so a harness that only looked for
    vacuity would go quietly decorative over time rather than all at once.
    """

    def test_a_sabotage_that_no_longer_applies_is_reported(self, tmp_path):
        finding = audit(STALE_BY_CONSTRUCTION, tmp_path / "stale")
        assert finding.verdict == "stale", finding.detail

    def test_it_is_not_reported_as_a_sound_arm(self, tmp_path):
        finding = audit(STALE_BY_CONSTRUCTION, tmp_path / "stale")
        with pytest.raises(MalformedArm, match="no longer match"):
            TestEveryArmAssertsSomething().test_no_sabotage_has_gone_stale((finding,))

    def test_a_check_that_no_longer_resolves_is_caught_before_it_can_score_sound(self, tmp_path):
        ghost = Arm(
            row="N2",
            asserts="a check that has been renamed away",
            sabotage=ARMS[0].sabotage,
            checks=("test_decode.py::TestM4TypedReferentsAndTheReceipt::test_renamed_away_at_some_point",),
        )
        # The trap: under sabotage it scores `sound`, because a usage error and a
        # failing check are the same exit code.
        assert audit(ghost, tmp_path / "ghost").verdict == "sound"
        # And the thing that springs it.
        assert baseline(ghost).verdict == "unresolved"

    def test_a_sabotage_matching_twice_is_stale_too(self, tmp_path):
        # Not pedantry: a pattern that matches twice mutates somewhere the arm
        # did not name, so its checks may fail for a reason the arm knows nothing
        # about — which reads as a sound arm and is not one.
        ambiguous = Arm(
            row="N2",
            asserts="a sabotage must name one site",
            sabotage=Sabotage(
                module="resolution.py", before="    def projection(self)", after="    def projection(self)"
            ),
            checks=STALE_BY_CONSTRUCTION.checks,
        )
        assert audit(ambiguous, tmp_path / "ambiguous").verdict == "stale"
