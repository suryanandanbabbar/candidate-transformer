import json
import os

from typer.testing import CliRunner

from candidate_transformer.cli.main import app

runner = CliRunner()


def test_transform_command_success():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(base_dir, "configs", "default.json")
    csv_path = os.path.join(base_dir, "sample_data", "recruiter.csv")

    result = runner.invoke(app, ["transform", "-c", config_path, "--source", f"recruiter_csv={csv_path}"])

    assert result.exit_code == 0
    output_json = json.loads(result.stdout)
    assert isinstance(output_json, list)
    assert len(output_json) > 0


def test_transform_command_multiple_sources():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(base_dir, "configs", "default.json")
    csv_path = os.path.join(base_dir, "sample_data", "recruiter.csv")
    ats_path = os.path.join(base_dir, "sample_data", "ats.json")

    result = runner.invoke(
        app,
        [
            "transform",
            "-c",
            config_path,
            "--source",
            f"recruiter_csv={csv_path}",
            "--source",
            f"ats_json={ats_path}",
        ],
    )
    assert result.exit_code == 0
    output_json = json.loads(result.stdout)
    assert len(output_json) > 0


def test_transform_command_missing_file():
    result = runner.invoke(app, ["transform", "--source", "recruiter_csv=fake.csv"])
    assert result.exit_code == 1


def test_transform_command_malformed_source():
    result = runner.invoke(app, ["transform", "--source", "recruiter_csv_fake.csv"])
    assert result.exit_code == 1


def test_transform_command_unknown_connector():
    result = runner.invoke(app, ["transform", "--source", "unknown_connector=fake.csv"])
    assert result.exit_code == 1


def test_transform_command_config_sources(tmp_path):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    csv_path = os.path.join(base_dir, "sample_data", "recruiter.csv")

    # Create a dynamic config with sources
    config_data = {
        "output": {"fields": []},
        "source_priorities": [],
        "sources": [{"connector": "recruiter_csv", "input": csv_path}],
    }

    config_file = tmp_path / "config_with_sources.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    result = runner.invoke(app, ["transform", "-c", str(config_file)])
    assert result.exit_code == 0
    output_json = json.loads(result.stdout)
    assert isinstance(output_json, list)
    assert len(output_json) > 0
