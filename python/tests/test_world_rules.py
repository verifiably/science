"""The fixture-bound rules store: identities, installation, and held resolution.

The identities here are *relations*, never literal digests. A pinned digest
constant would freeze the shipped fixture bytes, and those bytes are normative
content that later work replaces — a test that breaks when a normative fixture
gains a case is testing the fixture, not the identity rule.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
import zipfile
from hashlib import sha256
from pathlib import Path

import pytest
import yaml
from nodes.core.write_plan import CreateOp, DefaultExecutor
from test_root import patch_world_engine

import science.world.registry as world_module
from science import root
from science.errors import (
    EpochMalformed,
    RuleBindingUnknown,
    RuleCollision,
    RuleNonconformant,
    RuleNotHeld,
)
from science.identity import v1
from science.world import epoch, rules

SYMBOL = "sort_members"

SOURCE = b'''"""A minimal conforming rule, held only by this test."""


def sort_members(capture):
    return {"members": sorted(capture["members"])}
'''

OTHER_SOURCE = SOURCE + b"\n\n# a second conforming implementation of the same rule\n"

WRONG_SOURCE = b'''def sort_members(capture):
    return {"members": list(capture["members"])}
'''

RAISING_SOURCE = b'''def sort_members(capture):
    raise RuntimeError("this implementation does not run")
'''

FIXTURES: tuple[tuple[str, bytes], ...] = (
    ("sort.basic.yaml", b'input:\n  members: ["b", "a"]\nexpected:\n  members: ["a", "b"]\n'),
    ("sort.empty.yaml", b"input:\n  members: []\nexpected:\n  members: []\n"),
)


def bundle(
    *,
    symbol: str = SYMBOL,
    fixtures: tuple[tuple[str, bytes], ...] = FIXTURES,
    implementation: bytes = SOURCE,
) -> rules.RuleBundle:
    return rules.RuleBundle(symbol=symbol, fixtures=fixtures, implementation=implementation)


def make_world(tmp_path: Path) -> world_module.World:
    return world_module.World(world_module.WorldConfig(tmp_path / "world", "f" * 32, ()), DefaultExecutor)


def recording_world(tmp_path: Path) -> tuple[world_module.World, list[tuple[object, ...]]]:
    """A world whose executor keeps every plan it is handed."""
    plans: list[tuple[object, ...]] = []

    class Recorder:
        def __init__(self, world_root: Path) -> None:
            self.inner = DefaultExecutor(world_root)

        def execute(self, plan) -> None:
            plans.append(tuple(plan))
            self.inner.execute(plan)

    return world_module.World(world_module.WorldConfig(tmp_path / "world", "f" * 32, ()), Recorder), plans


def stored_members(world: world_module.World) -> dict[str, bytes]:
    base = world.config.world_root / "rules"
    if not base.exists():
        return {}
    return {
        str(path.relative_to(base)): path.read_bytes() for path in sorted(base.rglob("*")) if path.is_file()
    }


class TestTheTwoIdentities:
    def test_the_fixture_set_identity_is_the_pinned_domain_over_sorted_member_digests(self):
        expected = v1.digest(
            "science.fixture-set.v1",
            [[name, sha256(content).hexdigest()] for name, content in sorted(FIXTURES)],
        )

        assert rules.FIXTURE_SET_DOMAIN == "science.fixture-set.v1"
        assert rules.fixture_set_identity(FIXTURES) == expected

    def test_the_rule_identity_is_the_pinned_domain_over_symbol_and_fixture_set(self):
        expected = v1.digest(
            "science.enumeration-rule.v1",
            [SYMBOL, rules.fixture_set_identity(FIXTURES)],
        )

        assert rules.RULE_DOMAIN == "science.enumeration-rule.v1"
        assert rules.rule_identity(SYMBOL, FIXTURES) == expected

    def test_an_implementation_identity_is_the_member_content_digest_of_its_bytes(self):
        assert rules.implementation_identity(SOURCE) == sha256(SOURCE).hexdigest()
        assert rules.member_content_digest(SOURCE) == sha256(SOURCE).hexdigest()

    def test_member_order_moves_neither_identity(self):
        reversed_members = tuple(reversed(FIXTURES))

        assert rules.fixture_set_identity(reversed_members) == rules.fixture_set_identity(FIXTURES)
        assert rules.rule_identity(SYMBOL, reversed_members) == rules.rule_identity(SYMBOL, FIXTURES)
        assert rules.binding_for(bundle(fixtures=reversed_members)) == rules.binding_for(bundle())

    def test_the_symbol_moves_only_the_rule_identity(self):
        assert rules.rule_identity("other_symbol", FIXTURES) != rules.rule_identity(SYMBOL, FIXTURES)
        assert rules.fixture_set_identity(FIXTURES) == rules.fixture_set_identity(FIXTURES)
        assert rules.binding_for(bundle()).implementation_identity == rules.implementation_identity(SOURCE)

    def test_a_fixture_name_moves_both_identities(self):
        renamed = ((FIXTURES[0][0].replace("basic", "other"), FIXTURES[0][1]), FIXTURES[1])

        assert rules.fixture_set_identity(renamed) != rules.fixture_set_identity(FIXTURES)
        assert rules.rule_identity(SYMBOL, renamed) != rules.rule_identity(SYMBOL, FIXTURES)

    def test_fixture_bytes_move_both_identities(self):
        edited = ((FIXTURES[0][0], FIXTURES[0][1] + b"\n"), FIXTURES[1])

        assert rules.fixture_set_identity(edited) != rules.fixture_set_identity(FIXTURES)
        assert rules.rule_identity(SYMBOL, edited) != rules.rule_identity(SYMBOL, FIXTURES)

    def test_implementation_bytes_move_only_the_implementation_identity(self):
        one = rules.binding_for(bundle())
        two = rules.binding_for(bundle(implementation=OTHER_SOURCE))

        assert one.rule_identity == two.rule_identity
        assert one.implementation_identity != two.implementation_identity

    def test_a_bundle_refuses_an_absolute_or_escaping_fixture_name(self):
        for name in ("/sort.yaml", "nested/sort.yaml", "../sort.yaml", ""):
            with pytest.raises(ValueError):
                bundle(fixtures=((name, FIXTURES[0][1]),))

    def test_a_bundle_refuses_a_duplicate_fixture_name(self):
        with pytest.raises(ValueError):
            bundle(fixtures=(FIXTURES[0], FIXTURES[0]))


class TestTheRuleDocument:
    def test_the_rule_document_carries_exactly_the_symbol(self):
        content = rules.rule_document_bytes(SYMBOL)

        assert content == b"symbol: sort_members\n"
        assert rules.parse_rule_document(content) == SYMBOL

    @pytest.mark.parametrize(
        "content",
        [
            b"symbol: sort_members\nsymbol: other_symbol\n",  # duplicate key
            b"symbol: sort_members\nversion: 1\n",  # unknown key
            b"version: 1\n",  # missing symbol
            b"symbol: 12\n",  # not a symbol
            b"symbol:\n  - sort_members\n",  # not a scalar
            b"- symbol\n",  # not a mapping
            b"",  # empty
        ],
    )
    def test_the_rule_document_is_closed(self, content):
        with pytest.raises(RuleNotHeld):
            rules.parse_rule_document(content)


class TestInstallation:
    def test_rule_install_is_idempotent_and_refuses_collision_or_nonconformance(self, tmp_path):
        world = make_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())
        published = stored_members(world)

        # Exact, byte-identical reinstallation is idempotent success.
        assert rules.install_rule_binding(world, bundle()) == binding
        assert stored_members(world) == published

        # A second conforming implementation of the same rule is held beside it.
        second = rules.install_rule_binding(world, bundle(implementation=OTHER_SOURCE))
        assert second.rule_identity == binding.rule_identity
        assert second.implementation_identity != binding.implementation_identity
        assert set(stored_members(world)) > set(published)

        # An existing content-addressed path with different bytes refuses.
        for member in (
            f"{binding.rule_identity}/rule.yaml",
            f"{binding.rule_identity}/fixtures/{FIXTURES[0][0]}",
            f"{binding.rule_identity}/implementations/{binding.implementation_identity}",
        ):
            target = world.config.world_root / "rules" / member
            original = target.read_bytes()
            target.write_bytes(original + b"\n# raw swap\n")
            with pytest.raises(RuleCollision):
                rules.install_rule_binding(world, bundle())
            target.write_bytes(original)

        assert rules.install_rule_binding(world, bundle()) == binding

        # Nonconformance refuses before any transaction is submitted.
        for index, implementation in enumerate((WRONG_SOURCE, RAISING_SOURCE, b"", b"sort_members = 3\n")):
            fresh, plans = recording_world(tmp_path / f"refused-{index}")
            with pytest.raises(RuleNonconformant):
                rules.install_rule_binding(fresh, bundle(implementation=implementation))
            assert plans == []
            assert stored_members(fresh) == {}

    def test_install_submits_one_create_only_transaction_beneath_the_content_addressed_paths(self, tmp_path):
        world, plans = recording_world(tmp_path)

        binding = rules.install_rule_binding(world, bundle())

        assert len(plans) == 1
        assert all(isinstance(operation, CreateOp) for operation in plans[0])
        assert [operation.path for operation in plans[0]] == [
            f"rules/{binding.rule_identity}/rule.yaml",
            f"rules/{binding.rule_identity}/fixtures/{FIXTURES[0][0]}",
            f"rules/{binding.rule_identity}/fixtures/{FIXTURES[1][0]}",
            f"rules/{binding.rule_identity}/implementations/{binding.implementation_identity}",
        ]
        assert stored_members(world) == {
            f"{binding.rule_identity}/rule.yaml": rules.rule_document_bytes(SYMBOL),
            f"{binding.rule_identity}/fixtures/{FIXTURES[0][0]}": FIXTURES[0][1],
            f"{binding.rule_identity}/fixtures/{FIXTURES[1][0]}": FIXTURES[1][1],
            f"{binding.rule_identity}/implementations/{binding.implementation_identity}": SOURCE,
        }

        # The reinstall that changes nothing submits no second transaction.
        rules.install_rule_binding(world, bundle())
        assert len(plans) == 1

    @pytest.mark.parametrize(
        "document",
        [
            b"input:\n  members: []\nexpected:\n  members: []\nnote: extra\n",  # unknown key
            b"input:\n  members: []\ninput:\n  members: []\nexpected:\n  members: []\n",  # duplicate key
            b"input:\n  members: []\n",  # missing expected
            b"members: []\n",  # neither member
            b"",  # empty
        ],
    )
    def test_a_fixture_document_that_is_not_closed_refuses_as_nonconformance(self, tmp_path, document):
        world, plans = recording_world(tmp_path)

        with pytest.raises(RuleNonconformant):
            rules.install_rule_binding(world, bundle(fixtures=(("sort.basic.yaml", document),)))

        assert plans == []

    def test_a_bundle_with_no_fixture_is_refused(self, tmp_path):
        world, plans = recording_world(tmp_path)

        with pytest.raises(RuleNonconformant):
            rules.install_rule_binding(world, bundle(fixtures=()))

        assert plans == []

    def test_init_world_root_alone_holds_no_rule(self, monkeypatch, tmp_path):
        calls: list[tuple[str, object]] = []
        patch_world_engine(monkeypatch, calls)
        config = world_module.WorldConfig(tmp_path / "world", "1" * 32, ())

        root.init_world_root(config)
        world = root.open_world(config)

        assert not (config.world_root / "rules").exists()
        with pytest.raises(RuleNotHeld):
            rules._resolve_rule_binding(world, rules.binding_for(bundle()))
        for shipped in rules.shipped_rule_bundles():
            with pytest.raises(RuleNotHeld):
                rules._resolve_rule_binding(world, rules.binding_for(shipped))


class TestHeldResolution:
    def test_held_rule_recomputes_stored_symbol_and_fixtures(self, tmp_path):
        world = make_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())

        held = rules._resolve_rule_binding(world, binding)

        # The symbol comes from the stored document, and the source from the
        # exact named implementation — neither from the caller.
        assert held.binding == binding
        assert held.symbol == SYMBOL
        assert held.source == SOURCE
        assert held.invoke({"members": ["b", "a"]}) == {"members": ["a", "b"]}

        # The recomputation is over the stored bytes, and it closes on the
        # directory name.
        directory = world.config.world_root / "rules" / binding.rule_identity
        recovered = tuple(
            (path.name, path.read_bytes()) for path in sorted((directory / "fixtures").iterdir())
        )
        assert rules.fixture_set_identity(recovered) == rules.fixture_set_identity(FIXTURES)
        assert rules.rule_identity(held.symbol, recovered) == binding.rule_identity
        assert rules.implementation_identity(held.source) == binding.implementation_identity

    def test_an_unknown_binding_is_not_held(self, tmp_path):
        world = make_world(tmp_path)

        with pytest.raises(RuleNotHeld):
            rules._resolve_rule_binding(world, rules.binding_for(bundle()))

        binding = rules.install_rule_binding(world, bundle())
        unknown = rules.RuleBinding(binding.rule_identity, rules.implementation_identity(OTHER_SOURCE))
        with pytest.raises(RuleNotHeld):
            rules._resolve_rule_binding(world, unknown)

    @pytest.mark.parametrize(
        "sabotage",
        [
            "rule-document",
            "fixture-bytes",
            "fixture-added",
            "fixture-removed",
            "implementation-bytes",
            "implementation-absent",
        ],
    )
    def test_a_raw_swap_of_a_stored_member_unholds_the_binding(self, tmp_path, sabotage):
        world = make_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())
        directory = world.config.world_root / "rules" / binding.rule_identity

        if sabotage == "rule-document":
            (directory / "rule.yaml").write_bytes(rules.rule_document_bytes("other_symbol"))
        elif sabotage == "fixture-bytes":
            (directory / "fixtures" / FIXTURES[0][0]).write_bytes(FIXTURES[0][1] + b"\n")
        elif sabotage == "fixture-added":
            (directory / "fixtures" / "sort.extra.yaml").write_bytes(FIXTURES[1][1])
        elif sabotage == "fixture-removed":
            (directory / "fixtures" / FIXTURES[1][0]).unlink()
        elif sabotage == "implementation-bytes":
            (directory / "implementations" / binding.implementation_identity).write_bytes(OTHER_SOURCE)
        else:
            (directory / "implementations" / binding.implementation_identity).unlink()

        with pytest.raises(RuleNotHeld):
            rules._resolve_rule_binding(world, binding)

    def test_a_stored_implementation_that_stops_conforming_is_not_held(self, tmp_path):
        world = make_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())
        directory = world.config.world_root / "rules" / binding.rule_identity

        # Both the content name and its bytes are moved together, so only the
        # fixture run can catch this one.
        wrong = rules.implementation_identity(WRONG_SOURCE)
        (directory / "implementations" / wrong).write_bytes(WRONG_SOURCE)

        with pytest.raises(RuleNotHeld):
            rules._resolve_rule_binding(world, rules.RuleBinding(binding.rule_identity, wrong))


class TestTheShippedBundles:
    def test_four_bundles_ship_with_fixtures_and_distinct_identities(self):
        bundles = rules.shipped_rule_bundles()

        assert len(bundles) == 4
        assert len({shipped.symbol for shipped in bundles}) == 4
        assert len({rules.binding_for(shipped).rule_identity for shipped in bundles}) == 4
        for shipped in bundles:
            assert shipped.fixtures
            assert all(name.endswith(".yaml") and content for name, content in shipped.fixtures)
            assert shipped.symbol.encode("ascii") in shipped.implementation

    def test_the_composition_root_act_installs_and_holds_every_shipped_rule(self, tmp_path):
        world, plans = recording_world(tmp_path)

        bindings = root.install_shipped_world_rules(world)

        assert len(plans) == 4
        assert bindings == tuple(rules.binding_for(shipped) for shipped in rules.shipped_rule_bundles())
        for binding in bindings:
            held = rules._resolve_rule_binding(world, binding)
            assert held.binding == binding

        # The act is idempotent, and re-running it submits no further plan.
        assert root.install_shipped_world_rules(world) == bindings
        assert len(plans) == 4


def test_shipped_rules_install_from_a_built_wheel(tmp_path):
    """The package's fixtures and rule sources must survive packaging.

    A source-tree-only resource passes every other test in this file and then
    fails on an installed copy, so this arm builds the wheel, unpacks it away
    from the checkout, and installs from *that* copy in a child interpreter
    whose `science` is the unpacked one.
    """
    uv = shutil.which("uv")
    assert uv is not None, "the packaging arm needs `uv` on PATH; it is not skipped"
    project = Path(__file__).resolve().parents[1]
    distribution = tmp_path / "dist"
    subprocess.run(
        [uv, "build", "--wheel", "--out-dir", str(distribution)],
        cwd=project,
        check=True,
        capture_output=True,
    )
    unpacked = tmp_path / "unpacked"
    with zipfile.ZipFile(next(distribution.glob("*.whl"))) as archive:
        archive.extractall(unpacked)

    script = textwrap.dedent(
        """
        import json
        import sys
        from pathlib import Path

        from nodes.core.write_plan import DefaultExecutor

        from science.world import rules
        from science.world.registry import World, WorldConfig

        unpacked, world_root = sys.argv[1], sys.argv[2]
        assert Path(rules.__file__).is_relative_to(unpacked), rules.__file__

        world = World(WorldConfig(world_root, "a" * 32, ()), DefaultExecutor)
        bindings = [rules.install_rule_binding(world, shipped) for shipped in rules.shipped_rule_bundles()]
        print(
            json.dumps(
                {
                    "module": rules.__file__,
                    "bindings": [[one.rule_identity, one.implementation_identity] for one in bindings],
                    "symbols": [rules._resolve_rule_binding(world, one).symbol for one in bindings],
                }
            )
        )
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(unpacked), str(tmp_path / "world")],
        env={**os.environ, "PYTHONPATH": str(unpacked)},
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    # The child ran the unpacked wheel, not this checkout.
    assert Path(payload["module"]).is_relative_to(unpacked)
    assert not Path(payload["module"]).is_relative_to(project / "src")
    # And the wheel's own resources produce exactly the shipped identities: a
    # missing fixture member would move the rule identity, and a missing
    # fixture set refuses outright.
    shipped = rules.shipped_rule_bundles()
    assert payload["bindings"] == [
        [rules.binding_for(one).rule_identity, rules.binding_for(one).implementation_identity] for one in shipped
    ]
    assert payload["symbols"] == [one.symbol for one in shipped]


# --- explicit removal and its sever report ----------------------------------
#
# Epoch publication does not exist yet, so the retained epochs these arms need
# are authored here as raw closed eleven-member carriers under the cut's
# raw-write license. Only the four receipt members carry content this slice
# reads; the other seven are present, deterministic, closed placeholders whose
# exact shapes Task 9's publication pins.

RECEIPT_MEMBERS: tuple[str, ...] = (
    "producer-receipt.yaml",
    "retraction-receipt.yaml",
    "certification-receipt.yaml",
    "coreference-receipt.yaml",
)

RECEIPT_KINDS: dict[str, str] = {
    "producer-receipt.yaml": "producer",
    "retraction-receipt.yaml": "retraction-enumeration",
    "certification-receipt.yaml": "certification-enumeration",
    "coreference-receipt.yaml": "coreference-reduction",
}

COVERED_STATES: tuple[tuple[str, str], ...] = (
    ("aa" * 16, "1a" * 32),
    ("bb" * 16, "2b" * 32),
)

PLACEHOLDER_MEMBERS: dict[str, bytes] = {
    "address-map.yaml": b"entries: []\n",
    "producers-map.yaml": b"producers: []\n",
    "retraction-discovery-map.yaml": b"found: []\n",
    "coreference-map.yaml": b"pairs: []\n",
    "producer-snapshot.yaml": b"coverage: []\nproducers: []\n",
    "anchors.yaml": b"anchors: []\nworld_head: " + b"c" * 64 + b"\n",
    "coverage.yaml": b"coverage: []\n",
}


def subject_identity(marker: str) -> str:
    """A stand-in subject projection identity. Only its exactness matters here:
    the receipt identity digests the subject identity, never the subject."""
    return sha256(marker.encode("utf-8")).hexdigest()


def receipt_document(
    member: str,
    *,
    subject: str,
    binding: rules.RuleBinding,
    states: tuple[tuple[str, str], ...] = COVERED_STATES,
) -> bytes:
    return yaml.safe_dump(
        {
            "kind": RECEIPT_KINDS[member],
            "subject": subject,
            "corpus_states": [
                {"corpus_id": corpus_id, "corpus_state": corpus_state}
                for corpus_id, corpus_state in sorted(states)
            ],
            "rule_identity": binding.rule_identity,
            "implementation_identity": binding.implementation_identity,
        },
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")


def expected_receipt_identity(
    member: str,
    *,
    subject: str,
    binding: rules.RuleBinding,
    states: tuple[tuple[str, str], ...] = COVERED_STATES,
) -> str:
    """Spec §7.5's formula, written out here rather than borrowed from the
    module under test."""
    return v1.digest(
        "science.derivation-receipt.v1",
        [
            RECEIPT_KINDS[member],
            subject,
            [[corpus_id, corpus_state] for corpus_id, corpus_state in sorted(states)],
            binding.rule_identity,
            binding.implementation_identity,
        ],
    )


def author_epoch(world: world_module.World, receipts: dict[str, rules.RuleBinding], marker: str) -> str:
    """Write one closed eleven-member epoch carrier directly, and answer the
    packaging identity naming it (§6.2: `science.epoch.v1` over sorted
    `(member name, member content digest)` pairs)."""
    members = dict(PLACEHOLDER_MEMBERS)
    for member in RECEIPT_MEMBERS:
        members[member] = receipt_document(
            member, subject=subject_identity(f"{marker}:{member}"), binding=receipts[member]
        )
    assert set(members) == set(epoch.EPOCH_MEMBERS)
    packaging_identity = v1.digest(
        "science.epoch.v1",
        [[name, sha256(content).hexdigest()] for name, content in sorted(members.items())],
    )
    directory = world.config.world_root / "epochs" / packaging_identity
    directory.mkdir(parents=True)
    for name, content in sorted(members.items()):
        (directory / name).write_bytes(content)
    return packaging_identity


def epoch_members(world: world_module.World) -> dict[str, bytes]:
    base = world.config.world_root / "epochs"
    if not base.exists():
        return {}
    return {str(path.relative_to(base)): path.read_bytes() for path in sorted(base.rglob("*")) if path.is_file()}


class TestTheEpochInventory:
    def test_the_epoch_inventory_is_the_frozen_eleven_members(self):
        assert epoch.EPOCH_MEMBERS == (
            "address-map.yaml",
            "producers-map.yaml",
            "retraction-discovery-map.yaml",
            "coreference-map.yaml",
            "producer-snapshot.yaml",
            "producer-receipt.yaml",
            "retraction-receipt.yaml",
            "certification-receipt.yaml",
            "coreference-receipt.yaml",
            "anchors.yaml",
            "coverage.yaml",
        )
        assert len(set(epoch.EPOCH_MEMBERS)) == 11
        assert tuple(epoch.RECEIPT_KINDS) == RECEIPT_MEMBERS
        assert dict(epoch.RECEIPT_KINDS) == RECEIPT_KINDS
        assert set(epoch.RECEIPT_KINDS) < set(epoch.EPOCH_MEMBERS)
        assert epoch.RECEIPT_DOMAIN == "science.derivation-receipt.v1"


class TestExplicitRemoval:
    def test_rule_removal_is_exact_and_reports_severed_receipts(self, tmp_path):
        world, plans = recording_world(tmp_path)
        removed = rules.install_rule_binding(world, bundle())
        sibling = rules.install_rule_binding(world, bundle(implementation=OTHER_SOURCE))
        # A different rule sharing the *same* implementation bytes: the pair is
        # two digests, and only both together name what is removed.
        other_rule = rules.install_rule_binding(world, bundle(fixtures=(FIXTURES[0],)))
        assert sibling.rule_identity == removed.rule_identity
        assert sibling.implementation_identity != removed.implementation_identity
        assert other_rule.rule_identity != removed.rule_identity
        assert other_rule.implementation_identity == removed.implementation_identity

        # Two retained epochs. The first names the pair about to be removed in
        # three of its four receipts and a *sibling implementation of the same
        # rule* in the fourth; the second names the removed pair once and an
        # unrelated rule elsewhere.
        first_bindings = {
            "producer-receipt.yaml": removed,
            "retraction-receipt.yaml": removed,
            "certification-receipt.yaml": sibling,
            "coreference-receipt.yaml": removed,
        }
        second_bindings = {
            "producer-receipt.yaml": other_rule,
            "retraction-receipt.yaml": removed,
            "certification-receipt.yaml": other_rule,
            "coreference-receipt.yaml": sibling,
        }
        author_epoch(world, first_bindings, "first")
        author_epoch(world, second_bindings, "second")
        carriers = epoch_members(world)
        plans.clear()

        report = rules.remove_rule_binding(world, removed)

        # The report names the exact pair it unheld ...
        assert report.binding == removed
        # ... and every retained receipt that named it, sorted, and nothing else.
        assert report.severed_receipts == tuple(
            sorted(
                {
                    expected_receipt_identity(
                        member, subject=subject_identity(f"{marker}:{member}"), binding=binding
                    )
                    for marker, group in (("first", first_bindings), ("second", second_bindings))
                    for member, binding in group.items()
                    if binding == removed
                }
            )
        )
        assert len(report.severed_receipts) == 4

        # The sibling implementation of the same rule keeps its receipts: a
        # removed implementation is not a removed rule.
        for marker, member in (("first", "certification-receipt.yaml"), ("second", "coreference-receipt.yaml")):
            assert (
                expected_receipt_identity(
                    member, subject=subject_identity(f"{marker}:{member}"), binding=sibling
                )
                not in report.severed_receipts
            )

        # One delete plan, holding exactly the one implementation member.
        assert len(plans) == 1
        assert [(operation.op, operation.path) for operation in plans[0]] == [
            ("delete", f"rules/{removed.rule_identity}/implementations/{removed.implementation_identity}")
        ]
        assert plans[0][0].expected_digest == sha256(SOURCE).hexdigest()

        # Neither the shared normative half, nor the sibling, nor any epoch moved.
        assert stored_members(world) == {
            f"{removed.rule_identity}/rule.yaml": rules.rule_document_bytes(SYMBOL),
            f"{removed.rule_identity}/fixtures/{FIXTURES[0][0]}": FIXTURES[0][1],
            f"{removed.rule_identity}/fixtures/{FIXTURES[1][0]}": FIXTURES[1][1],
            f"{removed.rule_identity}/implementations/{sibling.implementation_identity}": OTHER_SOURCE,
            f"{other_rule.rule_identity}/rule.yaml": rules.rule_document_bytes(SYMBOL),
            f"{other_rule.rule_identity}/fixtures/{FIXTURES[0][0]}": FIXTURES[0][1],
            f"{other_rule.rule_identity}/implementations/{other_rule.implementation_identity}": SOURCE,
        }
        assert epoch_members(world) == carriers

        # The removed pair is unheld; its siblings are untouched.
        with pytest.raises(RuleNotHeld):
            rules._resolve_rule_binding(world, removed)
        assert rules._resolve_rule_binding(world, sibling).binding == sibling
        assert rules._resolve_rule_binding(world, other_rule).binding == other_rule

    def test_removing_the_final_implementation_deletes_the_rule_document_and_every_fixture(self, tmp_path):
        world, plans = recording_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())
        author_epoch(world, dict.fromkeys(RECEIPT_MEMBERS, binding), "only")
        plans.clear()

        report = rules.remove_rule_binding(world, binding)

        assert report.binding == binding
        assert len(report.severed_receipts) == 4
        assert len(plans) == 1
        assert [(operation.op, operation.path) for operation in plans[0]] == [
            ("delete", f"rules/{binding.rule_identity}/implementations/{binding.implementation_identity}"),
            ("delete", f"rules/{binding.rule_identity}/fixtures/{FIXTURES[0][0]}"),
            ("delete", f"rules/{binding.rule_identity}/fixtures/{FIXTURES[1][0]}"),
            ("delete", f"rules/{binding.rule_identity}/rule.yaml"),
        ]
        assert stored_members(world) == {}
        with pytest.raises(RuleNotHeld):
            rules._resolve_rule_binding(world, binding)

    def test_removing_one_of_several_implementations_leaves_the_rule_removable_again(self, tmp_path):
        world, plans = recording_world(tmp_path)
        first = rules.install_rule_binding(world, bundle())
        second = rules.install_rule_binding(world, bundle(implementation=OTHER_SOURCE))
        plans.clear()

        rules.remove_rule_binding(world, first)
        rules.remove_rule_binding(world, second)

        # The second removal is the final one, so it takes the shared half.
        assert len(plans) == 2
        assert [operation.path for operation in plans[0]] == [
            f"rules/{first.rule_identity}/implementations/{first.implementation_identity}"
        ]
        assert [operation.path for operation in plans[1]] == [
            f"rules/{second.rule_identity}/implementations/{second.implementation_identity}",
            f"rules/{second.rule_identity}/fixtures/{FIXTURES[0][0]}",
            f"rules/{second.rule_identity}/fixtures/{FIXTURES[1][0]}",
            f"rules/{second.rule_identity}/rule.yaml",
        ]
        assert stored_members(world) == {}

    @pytest.mark.parametrize("unknown", ["never-installed", "sibling-implementation", "already-removed"])
    def test_an_unknown_exact_pair_refuses_and_submits_no_delete_plan(self, tmp_path, unknown):
        world, plans = recording_world(tmp_path)
        binding = rules.binding_for(bundle())
        if unknown == "never-installed":
            pass
        elif unknown == "sibling-implementation":
            rules.install_rule_binding(world, bundle(implementation=OTHER_SOURCE))
        else:
            rules.install_rule_binding(world, bundle())
            rules.remove_rule_binding(world, binding)
        published = stored_members(world)
        plans.clear()

        with pytest.raises(RuleBindingUnknown):
            rules.remove_rule_binding(world, binding)

        assert plans == []
        assert stored_members(world) == published

    def test_an_unheld_stored_pair_is_not_removable(self, tmp_path):
        """Removal names a *held* pair. A stored implementation whose bytes no
        longer recompute their content name is not one."""
        world, plans = recording_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())
        target = (
            world.config.world_root
            / "rules"
            / binding.rule_identity
            / "implementations"
            / binding.implementation_identity
        )
        target.write_bytes(OTHER_SOURCE)
        published = stored_members(world)
        plans.clear()

        with pytest.raises(RuleBindingUnknown):
            rules.remove_rule_binding(world, binding)

        assert plans == []
        assert stored_members(world) == published

    def test_empty_directories_left_behind_are_ignored(self, tmp_path):
        world, plans = recording_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())
        directory = world.config.world_root / "rules" / binding.rule_identity
        plans.clear()

        rules.remove_rule_binding(world, binding)

        # Nonsemantic: the emptied directories may remain, and no plan swept them.
        assert directory.is_dir()
        assert (directory / "fixtures").is_dir()
        assert (directory / "implementations").is_dir()
        assert stored_members(world) == {}
        assert all(operation.op == "delete" for plan in plans for operation in plan)

        # They carry no hold, and they do not obstruct reinstallation.
        with pytest.raises(RuleBindingUnknown):
            rules.remove_rule_binding(world, binding)
        assert rules.install_rule_binding(world, bundle()) == binding
        assert rules._resolve_rule_binding(world, binding).binding == binding

    def test_a_world_with_no_retained_epoch_severs_nothing(self, tmp_path):
        world = make_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())

        assert rules.remove_rule_binding(world, binding).severed_receipts == ()

        # An epoch directory holding nothing is likewise nothing to sever.
        second = rules.install_rule_binding(world, bundle(implementation=OTHER_SOURCE))
        (world.config.world_root / "epochs").mkdir()
        assert rules.remove_rule_binding(world, second).severed_receipts == ()

    def test_two_retained_epochs_carrying_one_receipt_report_it_once(self, tmp_path):
        world = make_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())
        # Two carriers whose receipts agree in kind, subject, states and
        # binding are two carriers of the *same* receipt identity.
        first = author_epoch(world, dict.fromkeys(RECEIPT_MEMBERS, binding), "shared")
        members = {
            path.name: path.read_bytes()
            for path in (world.config.world_root / "epochs" / first).iterdir()
        }
        second = world.config.world_root / "epochs" / ("d" * 64)
        second.mkdir()
        for name, content in members.items():
            (second / name).write_bytes(content)

        report = rules.remove_rule_binding(world, binding)

        assert len(report.severed_receipts) == 4
        assert len(set(report.severed_receipts)) == 4

    @pytest.mark.parametrize(
        "sabotage",
        [
            "member-missing",
            "member-extra",
            "member-directory",
            "receipt-unknown-key",
            "receipt-missing-key",
            "receipt-duplicate-key",
            "receipt-kind-mismatch",
            "receipt-short-digest",
            "receipt-unsorted-states",
            "receipt-duplicate-state",
            "stray-epoch-entry",
            "stray-epoch-name",
        ],
    )
    def test_a_retained_carrier_that_is_not_closed_refuses_before_any_delete(self, tmp_path, sabotage):
        """Removal may make evidence unresolvable; it may not do so silently.
        A carrier it cannot read is a sever report it cannot write."""
        world, plans = recording_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())
        packaging_identity = author_epoch(world, dict.fromkeys(RECEIPT_MEMBERS, binding), "damaged")
        directory = world.config.world_root / "epochs" / packaging_identity
        receipt = directory / "producer-receipt.yaml"

        if sabotage == "member-missing":
            (directory / "coverage.yaml").unlink()
        elif sabotage == "member-extra":
            (directory / "notes.yaml").write_bytes(b"note: extra\n")
        elif sabotage == "member-directory":
            (directory / "coverage.yaml").unlink()
            (directory / "coverage.yaml").mkdir()
        elif sabotage == "receipt-unknown-key":
            receipt.write_bytes(receipt.read_bytes() + b"note: extra\n")
        elif sabotage == "receipt-missing-key":
            receipt.write_bytes(
                b"".join(
                    line + b"\n"
                    for line in receipt.read_bytes().splitlines()
                    if not line.startswith(b"rule_identity:")
                )
            )
        elif sabotage == "receipt-duplicate-key":
            receipt.write_bytes(receipt.read_bytes() + b"kind: producer\n")
        elif sabotage == "receipt-kind-mismatch":
            receipt.write_bytes(receipt.read_bytes().replace(b"kind: producer\n", b"kind: coreference-reduction\n"))
        elif sabotage == "receipt-short-digest":
            receipt.write_bytes(
                receipt.read_bytes().replace(
                    f"rule_identity: {binding.rule_identity}".encode(), b"rule_identity: abcdef"
                )
            )
        elif sabotage == "receipt-unsorted-states":
            document = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            document["corpus_states"] = list(reversed(document["corpus_states"]))
            receipt.write_bytes(yaml.safe_dump(document, sort_keys=True).encode("utf-8"))
        elif sabotage == "receipt-duplicate-state":
            document = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            document["corpus_states"] = [document["corpus_states"][0], document["corpus_states"][0]]
            receipt.write_bytes(yaml.safe_dump(document, sort_keys=True).encode("utf-8"))
        elif sabotage == "stray-epoch-entry":
            (world.config.world_root / "epochs" / "notes.yaml").write_bytes(b"note: extra\n")
        else:
            (world.config.world_root / "epochs" / "not-a-packaging-identity").mkdir()

        published = stored_members(world)
        plans.clear()
        with pytest.raises(EpochMalformed):
            rules.remove_rule_binding(world, binding)

        assert plans == []
        assert stored_members(world) == published

    def test_the_current_pointer_is_not_an_epoch_carrier(self, tmp_path):
        world = make_world(tmp_path)
        binding = rules.install_rule_binding(world, bundle())
        packaging_identity = author_epoch(world, dict.fromkeys(RECEIPT_MEMBERS, binding), "pointed")
        (world.config.world_root / "epochs" / "current").write_bytes(f"{packaging_identity}\n".encode())

        assert len(rules.remove_rule_binding(world, binding).severed_receipts) == 4

    def test_removal_is_reachable_through_the_package_facade(self):
        import science.world as facade

        assert facade.remove_rule_binding is rules.remove_rule_binding
        assert facade.RuleRemovalReport is rules.RuleRemovalReport
