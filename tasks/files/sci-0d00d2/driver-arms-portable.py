"""Criteria 6 and 7 (milestone design §5.6 C6, C7): cwd independence and MCP-select
then CLI-read, each arm a fresh `science mcp serve` over the same `science.toml`.

    arms.py <state> <run dir> [--workspace <mm program checkout>]

The workspace arm runs in the mm program's checkout; the unrelated arm in a fresh
temporary directory holding decoy `science.toml`, `science.yaml` and `corpus.yaml`; the
mcp arm selects over MCP and reads through fresh CLI processes while the server lives.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from common import State, run_cli, stop, write_json, wt
from walk import Server, complete

WORKSPACE = Path("<mm checkout>")


def select_health(server: Server, out: Path) -> None:
    reply = server.request("project-select", {"target": "health"}, "arm select")
    result = reply.get("result")
    if result is None or result["isError"]:
        stop(f"arm {out.name}: project-select health answered {reply}")
    (out / "select.txt").write_text(result["content"][0]["text"] + "\n")


def arm(state: State, name: str, cwd: Path, run_dir: Path) -> Path:
    out = run_dir / "arms" / name
    if out.exists():
        stop(f"{out} exists; each arm runs once per run directory")
    out.mkdir(parents=True)
    with Server(state.config, cwd, out / "serve.stderr") as server:
        select_health(server, out)
        if name == "mcp":
            (out / "next-cli.txt").write_text(run_cli(state.config, ["next"], cwd=cwd))
            (out / "next-project-mm.txt").write_text(
                run_cli(state.config, ["next", "--project", "multiple-myeloma"], cwd=cwd))
            (out / "projects-after.txt").write_text(run_cli(state.config, ["projects"], cwd=cwd))
        else:
            for command in ("status", "projects", "next"):
                (out / f"{command}.txt").write_text(run_cli(state.config, [command], cwd=cwd))
    (out / "cwd.txt").write_text(f"{cwd}\n")
    print(f"arm {name}: {cwd}")
    return out


def decoy() -> Path:
    path = Path(tempfile.mkdtemp(prefix="sci-0d00d2-decoy-"))
    (path / "science.toml").write_text('world_root = "/nowhere"\n')
    (path / "science.yaml").write_text("project: decoy\n")
    (path / "corpus.yaml").write_text("corpus: decoy\n")
    return path


def compare(run_dir: Path) -> dict:
    arms = run_dir / "arms"

    def same(a: Path, b: Path) -> bool:
        return a.read_bytes() == b.read_bytes()

    result = {
        "a_workspace_equals_unrelated": {
            name: same(arms / "workspace" / name, arms / "unrelated" / name)
            for name in ("status.txt", "projects.txt", "next.txt")},
        "b_arms_next_equal_walk_next_health": {
            arm: same(arms / arm / "next.txt", run_dir / "next-health.txt") for arm in ("workspace", "unrelated")},
        "c_mcp": {
            "next_cli_equals_next_health": same(arms / "mcp" / "next-cli.txt", run_dir / "next-health.txt"),
            "next_project_mm_equals_next_multiple_myeloma": same(
                arms / "mcp" / "next-project-mm.txt", run_dir / "next-multiple-myeloma.txt"),
            "projects_marks_health_selected": any(
                line.rstrip().endswith("(selected)") and " health @" in line
                for line in (arms / "mcp" / "projects-after.txt").read_text().splitlines()),
        },
    }
    result["all_equal"] = all(value for group in result.values() for value in group.values())
    write_json(arms / "compare.json", result)
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("state", type=Path)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    args = parser.parse_args(argv[1:])
    state = State(args.state)
    state.load_config()  # refuses a state bound to another world than its config's
    run_dir = args.run_dir.resolve()
    if run_dir.parent != state.runs or not complete(run_dir):
        stop(f"{run_dir} is not a completed walk of {state.path}")
    if not args.workspace.is_dir():
        stop(f"{args.workspace} is not a directory")
    arm(state, "workspace", args.workspace.resolve(), run_dir)
    unrelated = decoy()
    try:
        arm(state, "unrelated", unrelated, run_dir)
    finally:
        shutil.rmtree(unrelated)
    arm(state, "mcp", wt() / "python", run_dir)
    result = compare(run_dir)
    print(result)
    return 0 if result["all_equal"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
