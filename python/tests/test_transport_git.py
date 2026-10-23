"""The git transport: idempotent push, remote listing, corpus fetch, git's own authentication."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from beliefs.intents.publish import Destination
from beliefs.transport import local_listing, transport_files

from helpers.commons import GIT_ENV, Remotes, commit_count
from science import transport_git
from science.transport_git import GitTransport, GitTransportFault, production_git_env

CID = "0123456789abcdef0123456789abcdef"
DEST = Destination("remote", "https://remote.test/a")


@pytest.fixture
def remotes(tmp_path: Path) -> Remotes:
    (tmp_path / "remotes").mkdir()
    return Remotes(tmp_path / "remotes")


@pytest.fixture
def bare(remotes: Remotes) -> Path:
    return remotes.bare("a")


@pytest.fixture
def files(tmp_path: Path) -> dict[str, Path]:
    container = tmp_path / "container"
    (container / CID / "sub").mkdir(parents=True)
    (container / CID / "one.txt").write_text("one")
    (container / CID / "sub" / "two.txt").write_text("two")
    (container / f"{CID}.head-artifact.v1").write_text("head")
    return transport_files(container, CID)


def make(tmp_path: Path, remotes: Remotes, bare: Path) -> GitTransport:
    return GitTransport(tmp_path / "cache", author="t", remote_for=remotes.remote_for, env=GIT_ENV)


def test_push_then_listing_equals_local_listing(tmp_path, remotes, bare, files):
    transport = make(tmp_path, remotes, bare)
    assert transport.push(DEST, files) is None
    assert transport.listing(DEST, CID) == local_listing(files)
    assert commit_count(bare) == 1


def test_a_second_push_of_present_files_commits_nothing(tmp_path, remotes, bare, files):
    transport = make(tmp_path, remotes, bare)
    transport.push(DEST, files)
    assert transport.push(DEST, files) is None
    assert commit_count(bare) == 1


def test_a_fresh_cache_pushes_onto_an_existing_remote(tmp_path, remotes, bare, files):
    make(tmp_path, remotes, bare).push(DEST, files)
    other = GitTransport(tmp_path / "cache2", author="t", remote_for=remotes.remote_for, env=GIT_ENV)
    assert other.push(DEST, files) is None
    assert commit_count(bare) == 1


def test_push_failing_after_push_converges_on_retry(tmp_path, remotes, bare, files):
    transport = make(tmp_path, remotes, bare)
    transport.fail_after_push = True
    with pytest.raises(GitTransportFault):
        transport.push(DEST, files)
    transport.fail_after_push = False
    assert transport.push(DEST, files) is None
    assert commit_count(bare) == 1
    assert transport.listing(DEST, CID) == local_listing(files)


def test_push_failing_before_commit_leaves_the_remote_untouched(tmp_path, remotes, bare, files):
    transport = make(tmp_path, remotes, bare)
    transport.fail_after_files = 1
    with pytest.raises(GitTransportFault):
        transport.push(DEST, files)
    assert transport.listing(DEST, CID) == {}
    assert commit_count(bare) == 0


def test_a_rejected_push_is_retried_once_after_a_fetch(tmp_path, remotes, bare, files):
    transport = make(tmp_path, remotes, bare)
    rival = tmp_path / "rival"
    stage = transport._stage
    rivals = []

    def stage_after_a_concurrent_commit(destination, repo, named):
        if not rivals:  # the remote moves between this cache's fetch and its push
            subprocess.run(["git", "clone", "-q", str(bare), str(rival)], env=GIT_ENV, check=True, capture_output=True)
            (rival / "other.txt").write_text("x")
            for args in (["add", "-A"], ["commit", "-qm", "rival"], ["push", "-q", "origin", "HEAD:refs/heads/main"]):
                subprocess.run(["git", "-C", str(rival), *args], env=GIT_ENV, check=True, capture_output=True)
            rivals.append(1)
        return stage(destination, repo, named)

    transport._stage = stage_after_a_concurrent_commit
    assert transport.push(DEST, files) is None
    assert commit_count(bare) == 2
    assert transport.listing(DEST, CID) == local_listing(files)


def test_a_push_rejected_twice_raises(tmp_path, remotes, bare, files):
    transport = make(tmp_path, remotes, bare)
    hook = bare / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    with pytest.raises(GitTransportFault, match="https://remote.test/a"):
        transport.push(DEST, files)
    assert commit_count(bare) == 0


def test_listing_sees_an_extra_file_the_act_did_not_ask_for(tmp_path, remotes, bare, files):
    transport = make(tmp_path, remotes, bare)
    transport.push(DEST, files)
    rival = tmp_path / "rival"
    subprocess.run(["git", "clone", "-q", str(bare), str(rival)], env=GIT_ENV, check=True)
    (rival / CID / "extra.txt").write_text("extra")
    (rival / "unrelated.txt").write_text("elsewhere")
    for args in (["add", "-A"], ["commit", "-qm", "extra"], ["push", "-q", "origin", "HEAD:refs/heads/main"]):
        subprocess.run(["git", "-C", str(rival), *args], env=GIT_ENV, check=True, capture_output=True)
    listing = transport.listing(DEST, CID)
    assert f"{CID}/extra.txt" in listing
    assert "unrelated.txt" not in listing
    assert set(listing) == set(files) | {f"{CID}/extra.txt"}


def test_listing_of_an_empty_remote_is_empty(tmp_path, remotes, bare):
    assert make(tmp_path, remotes, bare).listing(DEST, CID) == {}


def test_fetch_corpus_materializes_the_root_and_sibling(tmp_path, remotes, bare, files):
    transport = make(tmp_path, remotes, bare)
    transport.push(DEST, files)
    into = tmp_path / "into"
    into.mkdir()
    root, sibling = transport.fetch_corpus(DEST, CID, into)
    assert root == into / CID
    assert (root / "one.txt").read_text() == "one" and (root / "sub" / "two.txt").read_text() == "two"
    assert sibling == b"head"


def test_fetch_corpus_of_an_absent_corpus_names_the_location(tmp_path, remotes, bare, files):
    transport = make(tmp_path, remotes, bare)
    transport.push(DEST, files)
    with pytest.raises(GitTransportFault, match="https://remote.test/a"):
        transport.fetch_corpus(DEST, "f" * 32, tmp_path)


def test_fetch_corpus_of_an_unreachable_remote_names_the_location(tmp_path):
    transport = GitTransport(tmp_path / "c", author="t", remote_for=lambda d: str(tmp_path / "nope.git"), env=GIT_ENV)
    with pytest.raises(GitTransportFault, match="https://remote.test/a"):
        transport.fetch_corpus(DEST, CID, tmp_path)


def test_production_env_keeps_gits_own_configuration_and_never_prompts(monkeypatch):
    monkeypatch.setenv("GIT_SSH_COMMAND", "ssh -i key")
    monkeypatch.setenv("SECRET_TOKEN", "x")
    monkeypatch.setenv("SSH_AUTH_SOCK", "/s")
    monkeypatch.delenv("GIT_CONFIG_GLOBAL", raising=False)
    banned = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
              "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR")
    for key in banned:
        monkeypatch.setenv(key, "/elsewhere")
    env = production_git_env("science abc")
    assert env["GIT_SSH_COMMAND"] == "ssh -i key" and env["SSH_AUTH_SOCK"] == "/s" and env["GIT_TERMINAL_PROMPT"] == "0"
    assert "SECRET_TOKEN" not in env and "GIT_CONFIG_GLOBAL" not in env and env["GIT_AUTHOR_NAME"] == "science abc"
    assert env["GIT_COMMITTER_EMAIL"] == "science abc@science.invalid"
    assert not any(key in env for key in banned)


def test_production_env_carries_the_counted_config_pairs(monkeypatch):
    monkeypatch.setattr(transport_git.os, "environ", {
        "PATH": "/bin", "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "a.b", "GIT_CONFIG_VALUE_0": "1",
        "GIT_CONFIG_KEY_1": "c.d", "GIT_CONFIG_VALUE_1": "2", "GIT_CONFIG_KEY_2": "e.f", "GIT_CONFIG_VALUE_2": "3"})
    env = production_git_env("t")
    assert env["GIT_CONFIG_KEY_1"] == "c.d" and env["GIT_CONFIG_VALUE_1"] == "2"
    assert "GIT_CONFIG_KEY_2" not in env


def test_an_injected_object_directory_never_reaches_the_transports_git(tmp_path, remotes, bare, files, monkeypatch):
    other = tmp_path / "other.git"
    subprocess.run(["git", "init", "--bare", str(other)], check=True, env=GIT_ENV, capture_output=True)
    monkeypatch.setattr(transport_git.os, "environ", {**GIT_ENV, "GIT_OBJECT_DIRECTORY": str(other / "objects")})
    env = production_git_env("t")
    assert env["HOME"] == GIT_ENV["HOME"] and env["GIT_CONFIG_GLOBAL"] == "/dev/null"
    assert "GIT_OBJECT_DIRECTORY" not in env
    GitTransport(tmp_path / "c", author="t", remote_for=lambda d: str(bare)).push(DEST, files)
    assert commit_count(bare) == 1
    assert sorted(p.name for p in (other / "objects").iterdir()) == ["info", "pack"]
    assert not any((other / "objects" / "pack").iterdir())


def test_test_env_isolates_git_from_the_host(tmp_path, remotes, bare, monkeypatch):
    captured: list[dict] = []
    real = subprocess.run

    def capture(*args, **kwargs):
        captured.append(kwargs["env"])
        return real(*args, **kwargs)

    monkeypatch.setattr(transport_git.subprocess, "run", capture)
    make(tmp_path, remotes, bare).listing(DEST, CID)
    assert captured
    assert all(e["GIT_CONFIG_GLOBAL"] == "/dev/null" and e["GIT_CONFIG_NOSYSTEM"] == "1" for e in captured)


def test_a_deleted_remote_branch_is_not_served_from_a_stale_tracking_ref(tmp_path, remotes, bare, files):
    transport = make(tmp_path, remotes, bare)
    transport.push(DEST, files)
    subprocess.run(["git", "-C", str(bare), "update-ref", "-d", "refs/heads/main"], env=GIT_ENV, check=True)
    assert commit_count(bare) == 0
    assert transport.listing(DEST, CID) == {}
    assert transport.push(DEST, files) is None
    assert commit_count(bare) == 1
    assert transport.listing(DEST, CID) == local_listing(files)


def test_a_hostile_remote_path_is_refused_and_writes_nothing_outside(tmp_path, remotes, bare):
    def git(*args, data=None):
        return subprocess.run(["git", "-C", str(bare), *args], env=GIT_ENV, input=data, check=True,
                              capture_output=True).stdout.strip().decode()

    blob = git("hash-object", "-w", "--stdin", data=b"evil")
    inner = git("hash-object", "--literally", "-t", "tree", "-w", "--stdin",
                data=b"100644 x\0" + bytes.fromhex(blob))
    cid_tree = git("hash-object", "--literally", "-t", "tree", "-w", "--stdin",
                   data=b"40000 ..\0" + bytes.fromhex(inner))
    root = git("hash-object", "--literally", "-t", "tree", "-w", "--stdin",
               data=b"100644 " + f"{CID}.head-artifact.v1".encode() + b"\0" + bytes.fromhex(blob)
               + b"40000 " + CID.encode() + b"\0" + bytes.fromhex(cid_tree))
    commit = git("commit-tree", root, "-m", "hostile")
    git("update-ref", "refs/heads/main", commit)
    transport = make(tmp_path, remotes, bare)
    into = tmp_path / "work" / "into"
    into.mkdir(parents=True)
    with pytest.raises(GitTransportFault, match="https://remote.test/a"):
        transport.fetch_corpus(DEST, CID, into)
    with pytest.raises(GitTransportFault, match="https://remote.test/a"):
        transport.listing(DEST, CID)
    assert list(into.iterdir()) == [] and list((tmp_path / "work").iterdir()) == [into]


def plant_tree(bare: Path, entries: list[tuple[str, str, bytes]]) -> None:
    """Commit on the bare remote's `main` a root tree of `(mode, name, blob bytes)` entries; mode `120000` makes a
    symlink entry whose blob is the link text."""
    def git(*args: str, data: bytes | None = None) -> str:
        return subprocess.run(["git", "-C", str(bare), *args], env=GIT_ENV, input=data, check=True,
                              capture_output=True).stdout.strip().decode()

    lines = [f"{mode} blob {git('hash-object', '-w', '--stdin', data=blob)}\t{name}" for mode, name, blob in entries]
    tree = git("mktree", data=("\n".join(lines) + "\n").encode())
    git("update-ref", "refs/heads/main", git("commit-tree", tree, "-m", "hostile"))


def test_a_push_onto_symlinks_in_a_hostile_remote_tree_writes_nothing_outside_the_cache(tmp_path, remotes, bare,
                                                                                        files):
    outside_dir, outside_file = tmp_path / "outside-dir", tmp_path / "outside.txt"
    outside_dir.mkdir()
    outside_file.write_bytes(b"keep")
    plant_tree(bare, [("120000", CID, str(outside_dir).encode()),
                      ("120000", f"{CID}.head-artifact.v1", str(outside_file).encode())])
    with pytest.raises(GitTransportFault, match="https://remote.test/a"):
        make(tmp_path, remotes, bare).push(DEST, files)
    assert outside_file.read_bytes() == b"keep"
    assert list(outside_dir.iterdir()) == []


def test_a_symlink_in_the_cache_tree_refuses_staging(tmp_path, remotes, bare, files):
    outside_file = tmp_path / "outside.txt"
    outside_file.write_bytes(b"keep")
    transport = make(tmp_path, remotes, bare)
    stage = transport._stage

    def stage_onto_a_planted_symlink(destination, repo, named):
        (repo / f"{CID}.head-artifact.v1").symlink_to(outside_file)
        return stage(destination, repo, named)

    transport._stage = stage_onto_a_planted_symlink
    with pytest.raises(GitTransportFault, match=f"https://remote.test/a.*{CID}.head-artifact.v1"):
        transport.push(DEST, files)
    assert outside_file.read_bytes() == b"keep"
    assert commit_count(bare) == 0
