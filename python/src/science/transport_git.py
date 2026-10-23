"""The git transport: publishes a corpus to a git remote and reads it back.

`push` is idempotent (a name already present with the same bytes commits nothing), `listing` reports what the
remote holds, and `fetch_corpus` materializes one corpus for `adopt`. Authentication is git's own: the
transport runs git under an allowlisted environment so its credential helpers and configuration stay reachable
while no repository-location override can aim it at another repository."""
from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path

from beliefs.intents.publish import Destination
from beliefs.transport import TransportAbandoned

GIT_PASSTHROUGH = ("PATH", "HOME", "USER", "LANG", "LC_ALL", "SSH_AUTH_SOCK", "XDG_CONFIG_HOME", "XDG_CACHE_HOME",
                   # git's authentication and configuration variables, by name (an allowlist: a repository- or
                   # object-location override such as GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE, GIT_OBJECT_DIRECTORY,
                   # GIT_ALTERNATE_OBJECT_DIRECTORIES, GIT_COMMON_DIR or GIT_NAMESPACE would aim the transport's
                   # commands or its object writes at another repository, and is never passed)
                   "GIT_SSH", "GIT_SSH_COMMAND", "GIT_ASKPASS", "GIT_PROXY_COMMAND", "GIT_CONFIG_GLOBAL",
                   "GIT_CONFIG_SYSTEM", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_COUNT", "GIT_SSL_CAINFO", "GIT_SSL_CAPATH")
_HEAD_SUFFIX = ".head-artifact.v1"


class GitTransportFault(Exception):
    """A transient failure: the act or its handler sees it, and a retry may succeed."""


def production_git_env(author: str) -> dict[str, str]:
    """The environment git runs under: the allowlisted variables present in `os.environ`, the counted
    `GIT_CONFIG_KEY_<n>`/`GIT_CONFIG_VALUE_<n>` pairs, no terminal prompt, and an identity derived from `author`."""
    env = {key: os.environ[key] for key in GIT_PASSTHROUGH if key in os.environ}
    for n in range(int(os.environ.get("GIT_CONFIG_COUNT", "0"))):
        for key in (f"GIT_CONFIG_KEY_{n}", f"GIT_CONFIG_VALUE_{n}"):
            if key in os.environ:
                env[key] = os.environ[key]
    env["GIT_TERMINAL_PROMPT"] = "0"
    email = f"{author}@science.invalid"
    env.update(GIT_AUTHOR_NAME=author, GIT_AUTHOR_EMAIL=email, GIT_COMMITTER_NAME=author, GIT_COMMITTER_EMAIL=email)
    return env


def identity_remote(destination: Destination) -> str:
    """The git remote of a destination: its locator itself."""
    return destination.locator


def _in_namespace(name: str, corpus_id: str) -> bool:
    return name == f"{corpus_id}{_HEAD_SUFFIX}" or name.startswith(f"{corpus_id}/")


class GitTransport:
    fail_after_files: int | None = None  # test seam: raise GitTransportFault after copying this many files, before commit
    fail_after_push: bool = False        # test seam: raise GitTransportFault after a successful push, before returning

    def __init__(self, cache: Path, *, author: str, remote_for: Callable[[Destination], str] = identity_remote,
                 env: Mapping[str, str] | None = None, git: str = "git", branch: str = "main") -> None:
        self._cache = Path(cache)
        self._remote_for = remote_for
        self._env = dict(production_git_env(author) if env is None else env)
        self._git = git
        self._branch = branch

    def push(self, destination: Destination, files: Mapping[str, Path]) -> TransportAbandoned | None:
        repo = self._sync(destination)
        corpus_id = next(iter(files)).split("/")[0].removesuffix(_HEAD_SUFFIX)
        for attempt in (1, 2):
            if self._stage(repo, files) is False:
                return None
            self._run(repo, "commit", "-q", "-m", f"publish {corpus_id}")
            pushed = self._run(repo, "push", "-q", "origin", f"HEAD:refs/heads/{self._branch}", check=False)
            if pushed.returncode == 0:
                if self.fail_after_push:
                    raise GitTransportFault(f"{destination.locator}: injected failure after push")
                return None
            if attempt == 2:
                raise GitTransportFault(f"{destination.locator}: push rejected twice: {self._message(pushed)}")
            self._sync(destination)  # a concurrent commit does not touch these names: fetch, reset, restage
        raise AssertionError("unreachable")

    def listing(self, destination: Destination, corpus_id: str) -> dict[str, str]:
        repo = self._sync(destination)
        return {name: sha256(self._blob(repo, name)).hexdigest() for name in self._names(repo, destination, corpus_id)}

    def fetch_corpus(self, destination: Destination, corpus_id: str, into: Path) -> tuple[Path, bytes]:
        repo = self._sync(destination)
        names = self._names(repo, destination, corpus_id)
        sibling = f"{corpus_id}{_HEAD_SUFFIX}"
        if sibling not in names or len(names) == 1:
            raise GitTransportFault(f"{destination.locator}: corpus {corpus_id} is absent")
        root = Path(into) / corpus_id
        for name in names:
            if name != sibling:
                target = Path(into) / name
                if not target.resolve().is_relative_to(Path(into).resolve()):
                    raise GitTransportFault(f"{destination.locator}: {name!r} escapes the destination")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(self._blob(repo, name))
        return root, self._blob(repo, sibling)

    # -- local clone ---------------------------------------------------------------------------------------

    def _run(self, repo: Path, *args: str, check: bool = True, text: bool = True) -> subprocess.CompletedProcess:
        done = subprocess.run([self._git, "-C", str(repo), *args], env=self._env, capture_output=True, text=text)
        if check and done.returncode != 0:
            raise GitTransportFault(f"git {args[0]} failed: {self._message(done)}")
        return done

    @staticmethod
    def _message(done: subprocess.CompletedProcess) -> str:
        err = done.stderr if isinstance(done.stderr, str) else done.stderr.decode(errors="replace")
        return err.strip()

    def _sync(self, destination: Destination) -> Path:
        """The cache clone for the destination, fetched, and reset to the remote branch when it has one."""
        repo = self._cache / sha256(destination.locator.encode()).hexdigest()[:16]
        remote = self._remote_for(destination)
        if not (repo / ".git").exists():
            repo.mkdir(parents=True, exist_ok=True)
            self._run(repo, "init", "-q", "-b", self._branch)
            self._run(repo, "remote", "add", "origin", remote)
        else:
            self._run(repo, "remote", "set-url", "origin", remote)
        fetched = self._run(repo, "fetch", "-q", "--prune", "origin", check=False)
        if fetched.returncode != 0:
            raise GitTransportFault(f"{destination.locator}: unreachable: {self._message(fetched)}")
        # --prune: a branch the remote no longer has must not survive as a stale remote-tracking ref
        if self._has_branch(repo):
            reset = self._run(repo, "reset", "-q", "--hard", f"origin/{self._branch}", check=False)
            if reset.returncode != 0:
                raise GitTransportFault(f"{destination.locator}: remote tree refused: {self._message(reset)}")
        elif self._run(repo, "rev-parse", "--verify", "--quiet", "HEAD", check=False).returncode == 0:
            # the remote has no branch: a commit left by an earlier failed push is discarded, not trusted
            self._run(repo, "update-ref", "-d", "HEAD")
            self._run(repo, "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", ".")
        return repo

    def _has_branch(self, repo: Path) -> bool:
        probe = self._run(repo, "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{self._branch}", check=False)
        return probe.returncode == 0

    def _stage(self, repo: Path, files: Mapping[str, Path]) -> bool:
        """Copy and stage the named files; False when the index then equals HEAD (nothing to commit)."""
        for copied, (name, source) in enumerate(files.items(), start=1):
            target = repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(Path(source).read_bytes())
            if copied == self.fail_after_files:
                raise GitTransportFault("injected failure before commit")
        self._run(repo, "add", "-A", "--", *files)
        return self._run(repo, "diff", "--cached", "--quiet", check=False).returncode != 0

    # -- remote reads --------------------------------------------------------------------------------------

    def _names(self, repo: Path, destination: Destination, corpus_id: str) -> list[str]:
        """The remote's names in the corpus namespace; a name the remote could use to escape it refuses."""
        if not self._has_branch(repo):
            return []
        tree = self._run(repo, "ls-tree", "-r", "--name-only", "-z", f"origin/{self._branch}")
        names = [name for name in tree.stdout.split("\0") if name and _in_namespace(name, corpus_id)]
        for name in names:
            if any(part in ("", ".", "..") for part in name.split("/")):
                raise GitTransportFault(f"{destination.locator}: hostile remote path {name!r}")
        return names

    def _blob(self, repo: Path, name: str) -> bytes:
        return self._run(repo, "cat-file", "blob", f"origin/{self._branch}:{name}", text=False).stdout
