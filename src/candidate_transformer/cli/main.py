import json

import typer

from candidate_transformer.api import CandidateTransformer
from candidate_transformer.config import PipelineConfig
from candidate_transformer.utils.logger import logger, setup_logging

app = typer.Typer(help="Candidate Transformer CLI")


@app.command()
def transform(
    source: list[str] = typer.Option([], "--source", "-s", help="Source definition in format 'connector=file_path'"),
    config_file: str | None = typer.Option(None, "--config", "-c", help="Path to JSON configuration file (optional)"),
    projection: str | None = typer.Option(None, "--projection", "-p", help="Path to JSON projection configuration (optional)"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level (INFO, DEBUG, WARNING, ERROR)"),
) -> None:
    """
    Transform input candidate data into a canonical profile.
    """
    import logging

    setup_logging(getattr(logging, log_level.upper(), logging.INFO))

    logger.info("Starting transformation")

    try:
        config = None
        if config_file:
            with open(config_file) as f:
                config_dict = json.load(f)
                config = PipelineConfig(**config_dict)
            transformer = CandidateTransformer(config)
        else:
            transformer = CandidateTransformer()
            config = transformer.config

        override_config = None
        if projection:
            from candidate_transformer.config import OutputConfig
            with open(projection) as f:
                proj_dict = json.load(f)
                # If projection has an "output" root, extract it. Otherwise assume it's the root.
                if "output" in proj_dict:
                    proj_dict = proj_dict["output"]
                override_config = OutputConfig(**proj_dict)

        sources_to_load = []

        if source:
            for s in source:
                if "=" not in s:
                    logger.error(
                        "Malformed source specification. Expected 'connector=file_path'",
                        source=s,
                    )
                    raise typer.Exit(code=1)
                connector, file_path = s.split("=", 1)
                sources_to_load.append((connector, file_path))
        elif config and getattr(config, "sources", None):
            for src in config.sources or []:
                sources_to_load.append((src.connector, src.input))
        else:
            logger.error("No sources provided. Provide --source or specify sources in configuration.")
            raise typer.Exit(code=1)

        from candidate_transformer.connectors.registry import connector_registry

        for connector, file_path in sources_to_load:
            if connector not in connector_registry.all():
                logger.error("Unknown connector", connector=connector)
                raise typer.Exit(code=1)

            try:
                with open(file_path) as f:
                    transformer.load(connector, f)
            except FileNotFoundError as e:
                logger.error("File not found", error=str(e), file=file_path)
                raise typer.Exit(code=1)

        result = transformer.export(override_config)

        logger.info("Transformation successful")
        # Pretty print output array
        typer.echo(json.dumps(result, indent=2))

    except typer.Exit:
        raise
    except Exception as e:
        logger.error("Transformation failed", error=str(e))
        raise typer.Exit(code=1)


@app.command()
def validate(
    config_file: str = typer.Option(..., "--config", "-c", help="Path to JSON configuration file"),
    input_json: str = typer.Option(..., "--input", "-i", help="Path to the JSON output to validate"),
) -> None:
    """Validate a JSON profile against a configuration schema."""
    import logging

    setup_logging(logging.INFO)
    from candidate_transformer.config import OutputConfig
    from candidate_transformer.validation.output_validation import OutputValidator

    logger.info("Validating JSON output", input_file=input_json)

    try:
        with open(config_file) as f:
            config_dict = json.load(f)
            output_config = OutputConfig(**config_dict.get("output", {}))

        with open(input_json) as f:
            data = json.load(f)

        validator = OutputValidator()
        if isinstance(data, list):
            for item in data:
                validator.validate(item, output_config)
        else:
            validator.validate(data, output_config)

        logger.info("Validation successful")
        typer.echo("Validation passed.")
    except Exception as e:
        logger.error("Validation failed", error=str(e))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
