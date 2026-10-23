"""`provider-inspect` and `provider-bind` (commons 1a, Task 7): B reads the world A's publication claims at A's
location, and binds that location to A's world when B passes the same world id."""
import dataclasses

import pytest

from helpers.commons import LOC_A, a_identity, read_rig, refused, with_remotes
from helpers.world import open_rig
from science.sharing import SharingRegistry, replay
from science.transport_git import GitTransport


def _ids(installations) -> tuple[str, str]:
    ids = a_identity(installations.a)
    return ids["corpus_id"], ids["world"]


def _section(text: str, title: str) -> dict[str, str]:
    """The `key: value` pairs under a KeyVals block titled `title`."""
    lines = text.splitlines()
    body = {}
    for line in lines[lines.index(f"{title}:") + 1:]:
        if not line.startswith("  "):
            break
        key, _, value = line.strip().partition(": ")
        body[key] = value
    return body


def _no_scratch_under(directory) -> bool:
    return not directory.exists() or not any(directory.iterdir())


def _bind(installations, inputs: dict, *, iid: str | None = None):
    with with_remotes(installations), open_rig(installations.b, ("provider-bind",)) as (d, _):
        return d.invoke("provider-bind", inputs, invocation_id=iid)


def _refuse_fetch(monkeypatch) -> None:
    monkeypatch.setattr(GitTransport, "fetch_corpus",
                        lambda *args, **kwargs: pytest.fail("provider-bind fetched before refusing"))


def test_inspect_reports_the_claimed_world_and_leaves_no_scratch(published):
    ids = a_identity(published.a)
    with with_remotes(published):
        text = read_rig(published.b, "provider-inspect").invoke(
            "provider-inspect", {"location": LOC_A, "corpus_id": ids["corpus_id"]}).text
    fields = _section(text, "publication")
    assert list(fields) == ["world", "marker", "artifact", "view", "verdict"]
    assert fields["world"] == ids["world"] and fields["marker"] == ids["marker"]
    assert fields["artifact"] == ids["artifact"] and fields["verdict"] == "validated"
    assert fields["view"].startswith("coord:") and "@" in fields["view"]
    assert _no_scratch_under(published.b.operations_root / "scratch" / "inspect")
    # Read-only: B's registry holds nothing.
    assert SharingRegistry(published.b.sharing_root).bindings() == {}


def test_inspect_of_an_absent_corpus_names_the_location(published):
    with with_remotes(published):
        r = refused(lambda: read_rig(published.b, "provider-inspect").invoke(
            "provider-inspect", {"location": LOC_A, "corpus_id": "0" * 32}))
    assert r.code == "invalid-input" and LOC_A in r.message and "absent" in r.message
    assert _no_scratch_under(published.b.operations_root / "scratch" / "inspect")


def test_inspect_of_a_local_path_refuses_naming_the_location(published):
    location = str(published.remotes / "a.git")
    r = refused(lambda: read_rig(published.b, "provider-inspect").invoke(
        "provider-inspect", {"location": location, "corpus_id": "0" * 32}))
    assert r.code == "invalid-input" and location in r.message and "https://" in r.message


def test_bind_with_the_claimed_world_records_the_line_then_the_binding(published):
    cid, world = _ids(published)
    text = _bind(published, {"location": LOC_A, "corpus_id": cid, "world": world}).text
    assert f"[pin] {cid} bound" in text
    registry = SharingRegistry(published.b.sharing_root)
    assert list(registry.bindings()) == [world]
    binding = registry.bindings()[world]
    assert binding.confirmed and binding.locations == (LOC_A,)
    # The line is the binding's evidence: a replay over B's ledgers finds the registry already holding it.
    assert replay(registry, published.b.operations_root) == ()
    assert _no_scratch_under(published.b.sharing_root / "scratch")


def test_bind_with_another_world_refuses_world_mismatch_and_writes_nothing(published):
    cid, world = _ids(published)
    other = "f" * 32
    r = refused(lambda: _bind(published, {"location": LOC_A, "corpus_id": cid, "world": other}))
    assert r.code == "world-mismatch" and r.data == {"claimed": world, "given": other}
    registry = SharingRegistry(published.b.sharing_root)
    assert replay(registry, published.b.operations_root) == ()  # no sharing line
    assert registry.bindings() == {}
    assert _no_scratch_under(published.b.sharing_root / "scratch")


@pytest.mark.parametrize("world, reason", [
    ("xyz", "32"),
    ("A" * 32, "32"),
    (None, "another world"),  # the reader's own world id
])
def test_bind_with_a_malformed_or_own_world_refuses_before_fetching(published, monkeypatch, world, reason):
    cid, _ = _ids(published)
    world = published.b.world.world_id if world is None else world
    _refuse_fetch(monkeypatch)
    r = refused(lambda: _bind(published, {"location": LOC_A, "corpus_id": cid, "world": world}))
    assert r.code == "invalid-input" and reason in r.message
    assert SharingRegistry(published.b.sharing_root).bindings() == {}


def test_bind_with_a_malformed_corpus_id_refuses_before_fetching(published, monkeypatch):
    _, world = _ids(published)
    _refuse_fetch(monkeypatch)
    r = refused(lambda: _bind(published, {"location": LOC_A, "corpus_id": "not-an-id", "world": world}))
    assert r.code == "invalid-input" and "corpus_id" in r.message


def test_bind_without_sharing_root_refuses_naming_the_key(published, monkeypatch):
    cid, world = _ids(published)
    _refuse_fetch(monkeypatch)
    unshared = dataclasses.replace(published, b=dataclasses.replace(published.b, sharing_root=None))
    r = refused(lambda: _bind(unshared, {"location": LOC_A, "corpus_id": cid, "world": world}))
    assert r.code == "invalid-input" and "sharing_root" in r.message


def test_a_crash_between_the_line_and_the_binding_is_repaired_by_replay(published, monkeypatch):
    cid, world = _ids(published)

    def crash(self, binding):
        raise RuntimeError("injected crash before the registry write")

    monkeypatch.setattr(SharingRegistry, "write_binding", crash)
    with pytest.raises(RuntimeError, match="injected crash"):
        _bind(published, {"location": LOC_A, "corpus_id": cid, "world": world})
    monkeypatch.undo()
    registry = SharingRegistry(published.b.sharing_root)
    assert registry.bindings() == {}
    (line,) = replay(registry, published.b.operations_root)
    assert line.transition == "bound" and line.world == world
    binding = registry.bindings()[world]
    assert binding.locations == (LOC_A,) and binding.confirmed and binding.bound_since == line.at


def test_the_bound_fixture_holds_a_confirmed_binding_of_a_location_to_a_world(bound):
    binding = SharingRegistry(bound.b.sharing_root).bindings()[bound.a.world.world_id]
    assert LOC_A in binding.locations and binding.confirmed
