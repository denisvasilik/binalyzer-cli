import pytest
import os

from click.testing import CliRunner

from binalyzer import Template, TemplateAutoCompletion, cli

TESTS_ABS_PATH = os.path.dirname(os.path.abspath(__file__))


def test_stdout():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "template",
            os.path.join(TESTS_ABS_PATH, "resources/test.bin"),
            os.path.join(TESTS_ABS_PATH, "resources/test.xml"),
            "binary-data-64.data-field-1.depth-field-124",
        ],
    )
    assert (
        result.output
        == "00000020: 64 54 77 6F 5F 30 00 00  08 61 64 64 54 77 6F 5F  dTwo_0...addTwo_\n"
        "00000030: 31 00 02 08 01 01 0A 15  03 07 00 20 00 20 01 6A  1.......... . .j\n"
    )
    assert result.exit_code == 0


def test_write_template_to_file():

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "template",
            os.path.join(TESTS_ABS_PATH, "resources/test.bin"),
            os.path.join(TESTS_ABS_PATH, "resources/test.xml"),
            "binary-data-64.data-field-1.depth-field-124",
            "--output",
            "/tmp/test.bin",
        ],
    )
    assert result.output == ""
    assert result.exit_code == 0


def test_missing_binary_file():
    runner = CliRunner()
    result = runner.invoke(cli, [])
    actual = result.output
    expected = 'Usage: binalyzer [OPTIONS] COMMAND [ARGS]...\n\nOptions:\n  --version  Show the Binalyzer version\n  --help     Show this message and exit.\n\nCommands:\n  dump      Dump file content using optional start and end positions.\n  json\n  rest      Run a local test server.\n  template  Dump file content using a template.\n'
    assert "Usage" in actual
    assert result.exit_code == 0


def test_missing_template_file():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["template", os.path.join(TESTS_ABS_PATH, "resources/test.bin")]
    )
    assert (
        result.output
        == "Usage: binalyzer template [OPTIONS] FILE TEMPLATE_FILE TEMPLATE_PATH\nTry \"binalyzer template --help\" for help.\n\nError: Missing argument \"TEMPLATE_FILE\".\n"
    )
    assert result.exit_code == 2


def test_missing_template():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "template",
            os.path.join(TESTS_ABS_PATH, "resources/test.bin"),
            os.path.join(TESTS_ABS_PATH, "resources/test.xml"),
        ],
    )
    assert (
        result.output
        == "Usage: binalyzer template [OPTIONS] FILE TEMPLATE_FILE TEMPLATE_PATH\nTry \"binalyzer template --help\" for help.\n\nError: Missing argument \"TEMPLATE_PATH\".\n"
    )
    assert result.exit_code == 2


@pytest.mark.skip()
def test_invalid_template():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "template",
            os.path.join(TESTS_ABS_PATH, "resources/test.bin"),
            os.path.join(TESTS_ABS_PATH, "resources/test.xml"),
            "binary-data-65.",
        ],
    )
    print(result.output)
    assert (
        result.output
        == "Usage: binalyzer template [OPTIONS] FILE TEMPLATE_FILE TEMPLATE_PATH\nTry 'binalyzer template --help' for help.\n\nError: Missing argument 'TEMPLATE_PATH'.\n"
    )
    assert result.exit_code == 2


def test_autocomplete():
    template = Template(name="template")
    template.children = [
        Template(name="data-field-1"),
        Template(name="data-field-2"),
        Template(name="data-field-3"),
        Template(name="data-field-4"),
    ]

    incomplete = "template.data"
    auto_completion = TemplateAutoCompletion()
    result = auto_completion._autocomplete(template, incomplete)

    assert len(result) == 4


def test_find_template():
    template = Template(name="template")
    template.children = [
        Template(name="data-field-1"),
        Template(name="data-field-2"),
        Template(name="data-field-3"),
        Template(name="data-field-4"),
    ]

    incomplete = "template.data"
    auto_completion = TemplateAutoCompletion()
    result = auto_completion._autocomplete(template, incomplete)

    assert len(result) == 4


def test_find_nested_template():
    template = Template(name="template")
    data_field_1 = Template(name="data-field-1")
    data_field_1.children = [Template(name="depth-field-1")]
    template.children = [
        data_field_1,
        Template(name="data-field-2"),
        Template(name="data-field-3"),
        Template(name="data-field-4"),
    ]

    incomplete = "template.data-field-1.depth"
    auto_completion = TemplateAutoCompletion()
    result = auto_completion._autocomplete(template, incomplete)

    assert len(result) == 1


def test_find_nothing():
    template = Template(name="template")
    data_field_1 = Template(name="data-field-1")
    data_field_1.children = [Template(name="depth-field-1")]
    template.children = [
        data_field_1,
        Template(name="data-field-2"),
        Template(name="data-field-3"),
        Template(name="data-field-4"),
    ]

    incomplete = "template.data-field-1.abcd"
    auto_completion = TemplateAutoCompletion()
    result = auto_completion._autocomplete(template, incomplete)

    assert len(result) == 0
