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
from nodes.core.write_plan import CreateOp, DefaultExecutor
from test_root import patch_world_engine

import science.world.registry as world_module
from science import root
from science.errors import RuleCollision, RuleNonconformant, RuleNotHeld
from science.identity import v1
from science.world import rules

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
