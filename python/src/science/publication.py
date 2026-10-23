"""Publishing a view to a destination: the module seams the publish commands read.

Only the seams stand here so far; Task 6 of the commons 1a plan fills the module in (destination parsing, the
transport choice, marker and binding fields). `REMOTE_FOR` maps a destination to the git remote its transport
pushes to, and `GIT_ENV` is the environment that transport's git runs under (`None`: the production one)."""
from __future__ import annotations

from collections.abc import Mapping

from science.transport_git import identity_remote

REMOTE_FOR = identity_remote
GIT_ENV: Mapping[str, str] | None = None
