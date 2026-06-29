import os

from typer.testing import CliRunner

from candidate_transformer.cli.main import app

runner = CliRunner()


def test_validate_command_success(tmp_path):
    # Create a temporary JSON output file to validate
    output_file = tmp_path / "output.json"
    output_file.write_text('[{"candidate_id": "1", "full_name": "Test"}]')

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(base_dir, "configs", "default.json")

    result = runner.invoke(app, ["validate", "-c", config_path, "-i", str(output_file)])

    assert result.exit_code == 0
    assert "Validation passed" in result.stdout


def test_validate_command_failure(tmp_path):
    # Create invalid output (missing candidate_id)
    output_file = tmp_path / "output.json"
    output_file.write_text('[{"full_name": "Test"}]')

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(base_dir, "configs", "default.json")

    result = runner.invoke(app, ["validate", "-c", config_path, "-i", str(output_file)])

    assert result.exit_code == 1
