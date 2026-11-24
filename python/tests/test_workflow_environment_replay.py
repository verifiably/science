"""Certified-host integration tests for cross-client workflow environment replay and MM lock execution."""
from __future__ import annotations

import gzip
import hashlib
import importlib.metadata
import json
import os
import re
import signal
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import pytest

from beliefs import stored
from beliefs.confinement import PROBE_DIGEST_KEY, PROBE_PATH, host_prerequisites
from beliefs.runrecord import decode_run_closure
from helpers.analysis import spec_inputs
from helpers.world import build_belief_world, write_config_for
from science.config import ReadContext, load_config
from uncertified_host import uncertified_host

_SCIENCE_PY_ROOT = Path(__file__).resolve().parents[1]


def _require_certified_confinement() -> None:
    reason = host_prerequisites()
    if reason is not None:
        pytest.skip(f"confinement unavailable: {reason}")
    if uncertified_host(os.environ):
        pytest.skip("certified tuple unavailable on this host: workflow environment replay requires certified tuple")


def _uv_cache_dir() -> str | None:
    res = subprocess.run(["uv", "cache", "dir"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    return None


def _build_wheel(wheel_dir: Path, name: str, version: str, files: dict[str, str]) -> Path:
    wheel_dir.mkdir(parents=True, exist_ok=True)
    dist = name.replace("-", "_")
    wheel_path = wheel_dir / f"{dist}-{version}-py3-none-any.whl"
    dist_info = f"{dist}-{version}.dist-info"
    metadata = f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
    wheel_meta = (
        "Wheel-Version: 1.0\n"
        "Generator: test-replay-fixture\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    )
    entries = {
        **files,
        f"{dist_info}/METADATA": metadata,
        f"{dist_info}/WHEEL": wheel_meta,
    }
    record_lines: list[str] = []
    with zipfile.ZipFile(wheel_path, "w") as zf:
        for rel, content in sorted(entries.items()):
            raw = content.encode("utf-8")
            zf.writestr(rel, raw)
            record_lines.append(f"{rel},sha256={hashlib.sha256(raw).hexdigest()},{len(raw)}")
        record_lines.append(f"{dist_info}/RECORD,,")
        zf.writestr(f"{dist_info}/RECORD", "\n".join(record_lines) + "\n")
    return wheel_path


def _clean_env(cache_dir: str | None) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if cache_dir:
        env["UV_CACHE_DIR"] = cache_dir
    return env


def _wait_for_socket(sock: Path, proc: subprocess.Popen[bytes], timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while not sock.exists():
        if proc.poll() is not None:
            out, err = proc.communicate(timeout=5)
            raise AssertionError(
                f"science serve exited prematurely ({proc.returncode}): stdout={out.decode()} stderr={err.decode()}"
            )
        if time.monotonic() > deadline:
            raise AssertionError(f"service socket never appeared at {sock}")
        time.sleep(0.05)


def _stop_service(proc: subprocess.Popen[bytes], sock: Path) -> None:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    assert proc.returncode in (0, 128 + signal.SIGTERM, -signal.SIGTERM), (
        f"science serve exited with unexpected code {proc.returncode}"
    )
    assert not sock.exists(), "science serve left its socket behind after SIGTERM"


def _cli(python_bin: Path, args: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(python_bin), "-m", "science.cli", *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=240,
    )


def _ref_from(text: str, prefix: str) -> str:
    return next(tok for tok in text.split() if tok.startswith(prefix))


def _assert_probe_receipts(closure) -> None:
    for phase_name, launch in (("planning", closure.occurrence.receipt.planning), ("execution", closure.occurrence.receipt.execution)):
        assert launch.instance is not None, f"{phase_name} missing instance attestation"
        assert (PROBE_PATH, "probe", "ro") in launch.instance.mounts, f"{phase_name} missing ro probe mount"
        probe_rows = [row for row in launch.rendered_environment if row[0] == PROBE_DIGEST_KEY]
        assert len(probe_rows) == 1, f"{phase_name} expected 1 probe digest row, got {probe_rows}"
        assert probe_rows[0][1] == "value"
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", probe_rows[0][2])


def test_cross_client_cli_derive_run_and_verify_with_selected_workflow_environment(
    certified_work, short_tmp, tmp_path
):
    _require_certified_confinement()
    cache_dir = _uv_cache_dir()
    base_env = _clean_env(cache_dir)

    # 1. Build locked workflow project (snakemake 8.11.4 + wf-replay-sentinel absent from both Science clients).
    wheels_dir = tmp_path / "wheels"
    sentinel_whl = _build_wheel(
        wheels_dir,
        "wf-replay-sentinel",
        "0.1.0",
        {"wf_replay_sentinel/__init__.py": 'SENTINEL = "from-workflow-venv-v1"\n'},
    )
    wf_project = tmp_path / "wf-project"
    wf_project.mkdir()
    (wf_project / "pyproject.toml").write_text(
        "[project]\n"
        'name = "wf-replay-demo"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.11"\n'
        'dependencies = ["snakemake==8.11.4", "wf-replay-sentinel==0.1.0"]\n\n'
        "[tool.uv.sources]\n"
        f'wf-replay-sentinel = {{ path = "{sentinel_whl}" }}\n'
    )
    lock_res = subprocess.run(
        ["uv", "lock", "--no-config", "--offline"],
        cwd=wf_project,
        env=base_env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if lock_res.returncode != 0:
        lock_res = subprocess.run(
            ["uv", "lock", "--no-config"],
            cwd=wf_project,
            env=base_env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    assert lock_res.returncode == 0, f"uv lock failed: {lock_res.stderr}"

    # 2. Build Client B venv: same Science/Beliefs editable sources + one inert extra distribution.
    inert_whl = _build_wheel(
        wheels_dir,
        "inert-client-pkg",
        "0.1.0",
        {"inert_client_pkg/__init__.py": "INERT = True\n"},
    )
    client_b_venv = tmp_path / "client-b-venv"
    sync_env = {**base_env, "UV_PROJECT_ENVIRONMENT": str(client_b_venv), "UV_NO_CONFIG": "1"}
    base_py = Path(os.path.realpath(sys.executable))
    sync_b = subprocess.run(
        ["uv", "--directory", str(_SCIENCE_PY_ROOT), "sync", "--frozen", "--no-python-downloads", "--python", str(base_py)],
        env=sync_env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert sync_b.returncode == 0, f"Client B uv sync failed: {sync_b.stderr}"
    client_b_py = client_b_venv / "bin" / "python"
    pip_b = subprocess.run(
        ["uv", "pip", "install", "--no-config", "--offline", "--no-deps", "--python", str(client_b_py), str(inert_whl)],
        env=base_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert pip_b.returncode == 0, f"Client B inert install failed: {pip_b.stderr}"

    # Verify Client A vs Client B package set difference and shared candidate editable paths BEFORE replay.
    client_a_py = Path(sys.executable)
    with pytest.raises(importlib.metadata.PackageNotFoundError):
        importlib.metadata.distribution("inert-client-pkg")
    with pytest.raises(importlib.metadata.PackageNotFoundError):
        importlib.metadata.distribution("wf-replay-sentinel")

    import beliefs as beliefs_mod
    import science as science_mod

    probe_b = subprocess.run(
        [
            str(client_b_py),
            "-c",
            (
                "import importlib.metadata, json, beliefs, science\n"
                "assert importlib.metadata.version('inert-client-pkg') == '0.1.0'\n"
                "try:\n"
                "    importlib.metadata.distribution('wf-replay-sentinel')\n"
                "    raise AssertionError('wf-replay-sentinel unexpectedly in Client B')\n"
                "except importlib.metadata.PackageNotFoundError:\n"
                "    pass\n"
                "print(json.dumps({'science': science.__file__, 'beliefs': beliefs.__file__}))\n"
            ),
        ],
        env=base_env,
        capture_output=True,
        text=True,
        check=True,
    )
    b_paths = json.loads(probe_b.stdout)
    assert Path(b_paths["science"]).resolve() == Path(science_mod.__file__).resolve()
    assert Path(b_paths["beliefs"]).resolve() == Path(beliefs_mod.__file__).resolve()

    # 3. Build disposable certified world and workflow bundles.
    cfg = build_belief_world(certified_work)
    sock = short_tmp / "replay-svc.sock"
    cfg_path = write_config_for(cfg, service_socket=sock)

    raw_file = tmp_path / "raw.tsv"
    raw_file.write_bytes(b"gene\tval\nPHF19\t7\n")

    derive_code = certified_work / "derive_bundle"
    (derive_code / "workflow").mkdir(parents=True)
    (derive_code / "workflow" / "Snakefile").write_text(
        'rule curate:\n'
        '    input: "inputs/raw.tsv"\n'
        '    output: "curated.tsv"\n'
        '    run:\n'
        '        import pathlib, wf_replay_sentinel\n'
        '        raw = pathlib.Path(input[0]).read_text().strip()\n'
        '        pathlib.Path(output[0]).write_text(f"{raw}\\n# {wf_replay_sentinel.SENTINEL}\\n")\n'
    )

    assess_code = certified_work / "assess_bundle"
    (assess_code / "workflow").mkdir(parents=True)
    (assess_code / "workflow" / "Snakefile").write_text(
        'rule analyze:\n'
        '    input: "inputs/curated.tsv"\n'
        '    output: "outputs/outcome.txt"\n'
        '    run:\n'
        '        import pathlib, wf_replay_sentinel\n'
        '        text = pathlib.Path(input[0]).read_text()\n'
        '        assert wf_replay_sentinel.SENTINEL in text\n'
        '        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n'
        '        pathlib.Path(output[0]).write_text("supported\\n")\n'
    )

    # 4. Run Client A attended service: dataset -> derive(--workflow-project) -> spec -> run(--workflow-environment) -> assess.
    svc_a = subprocess.Popen(
        [str(client_a_py), "-m", "science.cli", "serve", "--config", str(cfg_path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=base_env,
    )
    try:
        _wait_for_socket(sock, svc_a)

        ds_res = _cli(
            client_a_py,
            ["dataset", "--config", str(cfg_path), "--path", str(raw_file), "--title", "raw", "--locator", "accession:DEMO1"],
            env=base_env,
        )
        assert ds_res.returncode == 0, ds_res.stderr
        raw_ds_ref = _ref_from(ds_res.stdout, "dataset:")

        derive_res = _cli(
            client_a_py,
            [
                "derive",
                "--config", str(cfg_path),
                "--dataset", raw_ds_ref,
                "--code", str(derive_code),
                "--entrypoint", "derive_bundle/workflow/Snakefile",
                "--targets", "curated.tsv",
                "--title", "curated demo",
                "--workflow-project", str(wf_project),
            ],
            env=base_env,
        )
        assert derive_res.returncode == 0, derive_res.stderr
        derive_err_lines = derive_res.stderr.splitlines()
        assert len(derive_err_lines) == 1, f"expected 1 stderr JSON line: {derive_err_lines!r}"
        derive_meta = json.loads(derive_err_lines[0])
        env_key = derive_meta["workflow_environment"]
        assert re.fullmatch(r"[0-9a-f]{64}", env_key)
        prod_run_ref = _ref_from(derive_res.stdout, "run:")

        ctx_a = ReadContext.open(load_config(cfg_path))
        derived_ds_node = next(
            n for n in ctx_a.write_view().iter_stored() if n.kind == "dataset" and n.title == "curated demo"
        )
        curated_bytes = ctx_a.held_resources(derived_ds_node.id)["curated.tsv"].read_bytes()
        assert b"from-workflow-venv-v1" in curated_bytes

        sp_in = spec_inputs(cfg, target="proposition:p1", dataset=derived_ds_node.id)
        spec_argv = [
            "spec",
            "--config", str(cfg_path),
            "--target", sp_in["target"],
            "--dataset", sp_in["dataset"],
            "--estimand", sp_in["estimand"],
            "--standing", sp_in["standing"],
            "--evidence-mode", sp_in["evidence_mode"],
            "--method", sp_in["method"],
            "--assumptions", sp_in["assumptions"],
            "--falsification", sp_in["falsification"],
            "--interpretation-rule", sp_in["interpretation_rule"],
            "--equivalence-rule", sp_in["equivalence_rule"],
        ]
        for rp in sp_in["rule_procedures"]:
            spec_argv.extend(["--rule-procedures", rp])
        spec_res = _cli(client_a_py, spec_argv, env=base_env)
        assert spec_res.returncode == 0, spec_res.stderr
        spec_ref = _ref_from(spec_res.stdout, "analysis-spec:")

        run_res = _cli(
            client_a_py,
            [
                "run",
                "--config", str(cfg_path),
                "--spec", spec_ref,
                "--dataset", derived_ds_node.id,
                "--code", str(assess_code),
                "--entrypoint", "assess_bundle/workflow/Snakefile",
                "--targets", "outputs/outcome.txt",
                "--workflow-environment", env_key,
            ],
            env=base_env,
        )
        assert run_res.returncode == 0, run_res.stderr
        assess_run_ref = _ref_from(run_res.stdout, "run:")

        assess_res = _cli(
            client_a_py,
            ["assess", "--config", str(cfg_path), "--run", assess_run_ref],
            env=base_env,
        )
        assert assess_res.returncode == 0, assess_res.stderr
        assessment_ref = _ref_from(assess_res.stdout, "assessment:")
    finally:
        _stop_service(svc_a, sock)

    # 5. Start a FRESH attended service under Client B (different client package set) on the retained world.
    svc_b = subprocess.Popen(
        [str(client_b_py), "-m", "science.cli", "serve", "--config", str(cfg_path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=base_env,
    )
    try:
        _wait_for_socket(sock, svc_b)
        cmdline_b = Path(f"/proc/{svc_b.pid}/cmdline").read_bytes().split(b"\0")
        assert str(client_b_py).encode() in cmdline_b[0]

        ver_prod = _cli(
            client_b_py,
            [
                "verify",
                "--config", str(cfg_path),
                "--run", prod_run_ref,
                "--code", str(derive_code),
                "--entrypoint", "derive_bundle/workflow/Snakefile",
                "--workflow-environment", env_key,
            ],
            env=base_env,
        )
        assert ver_prod.returncode == 0, ver_prod.stderr
        prod_ver_ref = _ref_from(ver_prod.stdout, "verification:")

        ver_assess = _cli(
            client_b_py,
            [
                "verify",
                "--config", str(cfg_path),
                "--assessment", assessment_ref,
                "--code", str(assess_code),
                "--entrypoint", "assess_bundle/workflow/Snakefile",
                "--workflow-environment", env_key,
            ],
            env=base_env,
        )
        assert ver_assess.returncode == 0, ver_assess.stderr
        assess_ver_ref = _ref_from(ver_assess.stdout, "verification:")

        # Reopen world and decode all persisted run and verification records.
        reopened = ReadContext.open(load_config(cfg_path))
        view = reopened.write_view()

        for ver_ref, orig_ref in ((prod_ver_ref, prod_run_ref), (assess_ver_ref, assess_run_ref)):
            ver_node = view.get(ver_ref)
            facet = ver_node.facets["verification"]
            assert facet["verdict"] == "passed"
            assert facet["scope"] == "clean-environment"
            orig_id, replay_id = stored.verification_derivation(ver_node)
            assert orig_id == orig_ref
            assert replay_id != orig_ref
            orig_closure = decode_run_closure(view.get(orig_id))
            replay_closure = decode_run_closure(view.get(replay_id))
            assert orig_closure.recipe.identity() == replay_closure.recipe.identity()
            _assert_probe_receipts(orig_closure)
            _assert_probe_receipts(replay_closure)

        # 6. Intentionally mutate a captured library in the prepared venv without changing lock -> early refusal.
        runs_before = sum(1 for n in view.iter_stored() if n.kind == "run")
        venv_root = cfg.operations_root / "workflow-environments" / env_key / "venv"
        sentinel_files = list(venv_root.rglob("wf_replay_sentinel/__init__.py"))
        assert len(sentinel_files) == 1
        sentinel_files[0].write_text('SENTINEL = "mutated-workflow-venv-v2"\n')

        drift_res = _cli(
            client_b_py,
            [
                "verify",
                "--config", str(cfg_path),
                "--run", prod_run_ref,
                "--code", str(derive_code),
                "--entrypoint", "derive_bundle/workflow/Snakefile",
                "--workflow-environment", env_key,
            ],
            env=base_env,
        )
        assert drift_res.returncode == 3, drift_res.stdout + drift_res.stderr
        drift_meta = json.loads(drift_res.stderr.splitlines()[0])
        assert drift_meta["refusal"]["code"] == "kernel-refused"
        assert drift_meta["refusal"]["data"]["reason"] == "recipe-identity-mismatch"

        after_view = ReadContext.open(load_config(cfg_path)).write_view()
        assert sum(1 for n in after_view.iter_stored() if n.kind == "run") == runs_before
    finally:
        _stop_service(svc_b, sock)


def _resolve_mm_checkout() -> Path | None:
    res = subprocess.run(["tasks", "resolve", "mm", "--json"], capture_output=True, text=True)
    if res.returncode != 0:
        return None
    data = json.loads(res.stdout)
    results = data.get("results", [])
    if not results or not results[0].get("root"):
        return None
    root = Path(results[0]["root"])
    return root if (root / "pyproject.toml").is_file() and (root / "uv.lock").is_file() else None


def test_mm_lock_native_imports_and_gse24080_shell_rule_on_certified_host(
    certified_work, tmp_path, monkeypatch
):
    _require_certified_confinement()
    mm_root = _resolve_mm_checkout()
    if mm_root is None:
        pytest.skip("confinement unavailable: multiple-myeloma checkout not present on this host")

    from helpers.world import open_rig
    from science.refusal import Refused
    from science.workflow_environment import prepare_environment

    cache_dir = _uv_cache_dir()
    if cache_dir:
        monkeypatch.setenv("UV_CACHE_DIR", cache_dir)

    cfg = build_belief_world(certified_work)
    mm_key = prepare_environment(mm_root, cfg.operations_root)
    assert re.fullmatch(r"[0-9a-f]{64}", mm_key)

    # Part A: native imports and behavior of pandas, pyarrow, and xlrd in the selected confined runtime.
    raw_file = tmp_path / "mm_input.tsv"
    raw_file.write_bytes(b"gene\texpr\nPHF19\t12.5\nTP53\t8.25\n")

    native_code = certified_work / "mm_native_wf"
    (native_code / "workflow").mkdir(parents=True)
    (native_code / "workflow" / "Snakefile").write_text(
        'rule check_native:\n'
        '    input: "inputs/mm_input.tsv"\n'
        '    output: "summary.json", "table.parquet"\n'
        '    run:\n'
        '        import json, pathlib, pandas as pd, pyarrow as pa, pyarrow.parquet as pq, xlrd\n'
        '        df = pd.read_csv(input[0], sep="\\t")\n'
        '        table = pa.Table.from_pandas(df, preserve_index=False)\n'
        '        pq.write_table(table, output[1], compression="zstd")\n'
        '        roundtrip = pq.read_table(output[1]).to_pandas()\n'
        '        summary = {\n'
        '            "pandas": pd.__version__,\n'
        '            "pyarrow": pa.__version__,\n'
        '            "xlrd": xlrd.__version__,\n'
        '            "rows": roundtrip.to_dict(orient="records"),\n'
        '        }\n'
        '        pathlib.Path(output[0]).write_text(json.dumps(summary, sort_keys=True) + "\\n")\n'
    )

    with open_rig(cfg, ("dataset", "derive")) as (d, ctx):
        raw_id = _ref_from(
            d.invoke("dataset", {"path": str(raw_file), "title": "mm synthetic"}).text,
            "dataset:",
        )
        out = d.invoke(
            "derive",
            {
                "dataset": raw_id,
                "code": str(native_code),
                "entrypoint": "mm_native_wf/workflow/Snakefile",
                "targets": ["summary.json", "table.parquet"],
                "title": "mm native summary",
                "workflow_environment": mm_key,
            },
        )
        run_id = _ref_from(out.text, "run:")
        closure = decode_run_closure(ctx.write_view().get(run_id))
        _assert_probe_receipts(closure)
        ds_node = next(n for n in ctx.write_view().iter_stored() if n.kind == "dataset" and n.title == "mm native summary")
        summary = json.loads(ctx.held_resources(ds_node.id)["summary.json"].read_text())
        assert summary["pandas"] == "2.3.3"
        assert summary["pyarrow"] == "25.0.1"
        assert summary["xlrd"] == "2.0.2"
        assert summary["rows"] == [{"gene": "PHF19", "expr": 12.5}, {"gene": "TP53", "expr": 8.25}]

        # Part B: representative GSE24080 shell rule with synthetic gzipped series matrix input.
        gse_raw = tmp_path / "gse_raw"
        gse_raw.mkdir()
        matrix_gz = gse_raw / "GSE24080_series_matrix.txt.gz"
        matrix_text = (
            '!Series_title\t"Synthetic GSE24080"\n'
            "!series_matrix_table_begin\n"
            '"ID_REF"\t"GSM1"\t"GSM2"\n'
            '"200001_at"\t10.5\t11.25\n'
            "!series_matrix_table_end\n"
        )
        matrix_gz.write_bytes(gzip.compress(matrix_text.encode("utf-8"), mtime=0))
        gse_raw_id = _ref_from(
            d.invoke("dataset", {"path": str(gse_raw), "title": "gse24080 synthetic"}).text,
            "dataset:",
        )

        gse_code = certified_work / "gse24080_shell_probe"
        (gse_code / "scripts").mkdir(parents=True)
        (gse_code / "scripts" / "expression.py").write_bytes(
            (mm_root / "workflows" / "gse24080" / "scripts" / "expression.py").read_bytes()
        )
        (gse_code / "Snakefile").write_text(
            "from pathlib import Path\n"
            'SCRIPTS = Path(workflow.basedir) / "scripts"\n'
            "rule expression:\n"
            '    input: "inputs/GSE24080_series_matrix.txt.gz"\n'
            '    output: "expression.parquet", "series_metadata.json"\n'
            '    shell: "python -I {SCRIPTS}/expression.py {input[0]} ."\n'
        )
        with pytest.raises(Refused) as shell_refusal:
            d.invoke(
                "derive",
                {
                    "dataset": gse_raw_id,
                    "code": str(gse_code),
                    "entrypoint": "gse24080_shell_probe/Snakefile",
                    "targets": ["expression.parquet", "series_metadata.json"],
                    "title": "gse24080 shell probe",
                    "workflow_environment": mm_key,
                },
            )
        assert shell_refusal.value.refusal.code == "kernel-refused"
        assert shell_refusal.value.refusal.data["kind"] == "RunRefused"
        assert shell_refusal.value.refusal.data["reason"] == "execution-failed"
        detail = shell_refusal.value.refusal.data.get("detail", "")
        assert detail, "expected concrete execution failure detail for GSE24080 shell rule"
