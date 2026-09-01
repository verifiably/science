from pathlib import Path

import pytest

from science.schema import (
    Declaration, DeclarationError, handler_module,
    load_command_tree, load_declaration,
)

KIND_ACTS = {
    "note": frozenset({"corpus-write"}),
    "run": frozenset({"run", "corpus-write"}),
}
CONTRACT_KINDS = frozenset(KIND_ACTS)


def write_command(root: Path, name: str, toml: str, prompt: str = "Do it.") -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "command.toml").write_text(toml)
    (d / "prompt.md").write_text(prompt)
    return d


GOOD = """
schema_version = 1
name = "status"
purpose = "Show the world."
write_class = "read-only"
output_budget = 16384

[inputs.corpus]
type = "string"
required = false
doc = "Restrict to one corpus."
"""


def test_good_declaration_loads(tmp_path):
    d = write_command(tmp_path, "status", GOOD)
    decl = load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert decl.name == "status"
    assert decl.write_class.kind == "read-only"
    assert decl.output_budget == 16384
    assert decl.inputs[0].name == "corpus" and not decl.inputs[0].required


@pytest.mark.parametrize("bad_name", ["Continue", "serve", "x" * 33, "9lives", "a_b", "a--b"])
def test_bad_names_refused(tmp_path, bad_name):
    toml = GOOD.replace('name = "status"', f'name = "{bad_name}"')
    d = write_command(tmp_path, "cmd", toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_newline_terminated_command_name_refused(tmp_path):
    toml = GOOD.replace('name = "status"', 'name = "status\\n"')
    d = write_command(tmp_path, "status", toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_newline_terminated_input_name_refused(tmp_path):
    toml = GOOD + '\n[inputs."extra\\n"]\ntype = "string"\nrequired = false\ndoc = "x"\n'
    d = write_command(tmp_path, "status", toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_reserved_input_refused(tmp_path):
    toml = GOOD + '\n[inputs.cursor]\ntype = "string"\nrequired = false\ndoc = "x"\n'
    d = write_command(tmp_path, "status", toml)
    with pytest.raises(DeclarationError) as e:
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert "cursor" in str(e.value)


def test_directory_name_mismatch_refused(tmp_path):
    d = write_command(tmp_path, "other", GOOD)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_enum_requires_choices_and_required_forbids_default(tmp_path):
    bad_enum = GOOD + '\n[inputs.mode]\ntype = "enum"\nrequired = true\ndoc = "x"\n'
    d = write_command(tmp_path, "status", bad_enum)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    bad_default = GOOD + '\n[inputs.x]\ntype = "string"\nrequired = true\ndefault = "y"\ndoc = "x"\n'
    d2 = write_command(tmp_path, "status2", bad_default.replace('name = "status"', 'name = "status2"'))
    with pytest.raises(DeclarationError):
        load_declaration(d2, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


MINTS = """
schema_version = 1
name = "mint-run"
purpose = "Fixture."
write_class = "mints:run,note"
output_budget = 4096

[write.routes]
run = "run"
"""


def test_mints_routes_resolve(tmp_path):
    d = write_command(tmp_path, "mint-run", MINTS)
    decl = load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert decl.write_class.kinds == ("note", "run")
    assert decl.write_class.routes == {"note": "corpus-write", "run": "run"}


def test_ambiguous_kind_without_route_refused(tmp_path):
    toml = MINTS.replace("[write.routes]\nrun = \"run\"\n", "")
    d = write_command(tmp_path, "mint-run", toml)
    with pytest.raises(DeclarationError) as e:
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert "run" in str(e.value)


def test_route_key_outside_kinds_and_inadmissible_route_refused(tmp_path):
    stray = MINTS + 'dataset = "run"\n'
    d = write_command(tmp_path, "mint-run", stray)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    wrong = MINTS.replace('run = "run"', 'run = "holdings"')
    d2 = write_command(tmp_path, "mint-run2", wrong.replace("mint-run", "mint-run2"))
    with pytest.raises(DeclarationError):
        load_declaration(d2, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_unknown_kind_refused(tmp_path):
    toml = MINTS.replace("run,note", "widget").replace('[write.routes]\nrun = "run"\n', "")
    d = write_command(tmp_path, "mint-run", toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_tree_refuses_duplicates_and_lists_all(tmp_path):
    write_command(tmp_path, "status", GOOD)
    write_command(tmp_path, "mint-run", MINTS)
    decls = load_command_tree(tmp_path, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert [d.name for d in decls] == ["mint-run", "status"]


def test_handler_module_mapping():
    assert handler_module("mint-run") == "science.commands.mint_run"


def test_bool_never_passes_an_int_field(tmp_path):
    for bad in ('schema_version = true', 'output_budget = true'):
        field = bad.split(" ")[0]
        toml = GOOD.replace(f"{field} = " + ("1" if field == "schema_version" else "16384"), bad)
        d = write_command(tmp_path, "status", toml)
        with pytest.raises(DeclarationError):
            load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
        import shutil; shutil.rmtree(d)


def test_default_is_type_checked_at_build(tmp_path):
    bad_type = GOOD + '\n[inputs.n]\ntype = "int"\nrequired = false\ndefault = "three"\ndoc = "x"\n'
    d = write_command(tmp_path, "status", bad_type)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    bad_enum = GOOD.replace('name = "status"', 'name = "st2"') + '\n[inputs.m]\ntype = "enum"\nrequired = false\nchoices = ["a"]\ndefault = "z"\ndoc = "x"\n'
    d2 = write_command(tmp_path, "st2", bad_enum)
    with pytest.raises(DeclarationError):
        load_declaration(d2, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_malformed_toml_is_a_declaration_error(tmp_path):
    d = write_command(tmp_path, "status", "this = is not [ toml")
    with pytest.raises(DeclarationError) as e:
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert "TOML" in str(e.value)


def test_hyphenated_input_name_refused(tmp_path):
    toml = GOOD + '\n[inputs.multi-word]\ntype = "string"\nrequired = false\ndoc = "x"\n'
    d = write_command(tmp_path, "status", toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_multiline_purpose_refused(tmp_path):
    toml = GOOD.replace('purpose = "Show the world."', 'purpose = "Two\\nlines."')
    d = write_command(tmp_path, "status", toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_stray_file_in_command_directory_refused(tmp_path):
    d = write_command(tmp_path, "status", GOOD)
    (d / "notes.txt").write_text("stray")
    with pytest.raises(DeclarationError) as e:
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert "notes.txt" in str(e.value)


BASE = """
schema_version = 1
name = "status"
purpose = "Show the world."
write_class = "read-only"
output_budget = 16384
"""


@pytest.mark.parametrize("mutation", [
    'inputs = "nope"',
    '[write]\nextra = 1',
    'write = "x"',
    '[write]\nroutes = "run"',
    'reads = "families"',
    '[reads]\nfamilies = "registry"',
    '[reads]\nextra = []',
    '[inputs.m]\ntype = "enum"\nrequired = false\nchoices = "ab"\ndoc = "x"',
])
def test_malformed_tables_are_declaration_errors(tmp_path, mutation):
    d = write_command(tmp_path, "status", BASE + mutation + "\n")
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_list_input_type_is_a_declaration_error(tmp_path):
    toml = GOOD + '\n[inputs.bad]\ntype = []\nrequired = false\ndoc = "x"\n'
    d = write_command(tmp_path, "status", toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_nested_list_enum_choice_is_a_declaration_error(tmp_path):
    toml = GOOD.replace('name = "status"', 'name = "st2"') + '\n[inputs.mode]\ntype = "enum"\nrequired = false\nchoices = [["a"]]\ndoc = "x"\n'
    d = write_command(tmp_path, "st2", toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
