# Candidate Transformer

A production-grade Python framework for converting heterogeneous candidate information into unified canonical profiles.

## Installation

```bash
# Standard installation
pip install candidate-transformer

# Development installation
git clone https://github.com/example/candidate-transformer.git
cd candidate-transformer
pip install -e ".[dev]"
```

## Architecture

```mermaid
flowchart TD
    A[Connectors (CSV, JSON, Text)] -->|RawRecord| B[Extraction]
    B -->|Dict| C[Normalization]
    C -->|Dict| D[Entity Resolution]
    D -->|Dict| E[Conflict Resolution]
    E -->|Candidate| F[Confidence Scoring]
    F -->|Candidate| G[Validation]
    G -->|Candidate| H[Projection Layer]
    H -->|Projected JSON| I[Output]
```

## Quick Start

### Python API

```python
from candidate_transformer import CandidateTransformer, PipelineConfig
import json

# Initialize the facade (loads default.json automatically if no config provided)
transformer = CandidateTransformer()

# Load heterogeneous data sources
with open('sample_data/recruiter.csv', 'r') as f:
    transformer.load('recruiter_csv', f)

with open('sample_data/ats.json', 'r') as f:
    transformer.load('ats_json', f)

# Execute pipeline and export JSON
output = transformer.export()
print(json.dumps(output, indent=2))
```

### CLI Execution

The CLI offers a powerful and flexible interface for transforming, projecting, and validating candidate data from heterogeneous sources. Below are the most common workflows, command patterns, and options.

#### 1. Transform data (single source)

To transform a single data source, specify the connector and file path using the `--source` argument:
```bash
candidate-transformer transform \
    --source recruiter_csv=sample_data/recruiter.csv
```
Here, `connector=file_path` (e.g., `recruiter_csv=sample_data/recruiter.csv`) selects the connector used to parse the file. Supported connectors include `recruiter_csv`, `ats_json`, `resume_text`, etc.

#### 2. Transform data (multiple heterogeneous sources)

You can ingest and merge multiple data sources in a single command. All sources are loaded together and merged into canonical candidate profiles:
```bash
candidate-transformer transform \
    --source recruiter_csv=sample_data/recruiter.csv \
    --source ats_json=sample_data/ats.json \
    --source resume_text=sample_data/resume.txt \
    --config configs/default.json
```
Each `--source` specifies a connector and file. The system deduplicates and merges all incoming records into unified candidates.

#### 3. Use runtime projections

You can specify different projection schemas at runtime using the `--projection` argument to control the output shape:

- **Minimal projection** (outputs only minimal identity fields):
    ```bash
    candidate-transformer transform \
        --source recruiter_csv=sample_data/recruiter.csv \
        --projection configs/projections/minimal.json
    ```
    Produces a minimal JSON output with only the most essential candidate fields.

- **Recruiter projection** (fields tailored for recruiter workflows):
    ```bash
    candidate-transformer transform \
        --source recruiter_csv=sample_data/recruiter.csv \
        --projection configs/projections/recruiter.json
    ```
    Outputs all fields typically required by recruiters.

- **ATS projection** (fields for applicant tracking systems):
    ```bash
    candidate-transformer transform \
        --source recruiter_csv=sample_data/recruiter.csv \
        --projection configs/projections/ats.json
    ```
    Produces output compatible with ATS data models.

- **Analytics projection** (fields for analytics/reporting):
    ```bash
    candidate-transformer transform \
        --source recruiter_csv=sample_data/recruiter.csv \
        --projection configs/projections/analytics.json
    ```
    Outputs fields optimized for downstream analytics and reporting.

#### 4. Validate generated output

After running a transformation, you can validate the output JSON against the requested projection schema:
```bash
# First, generate output
candidate-transformer transform \
    --source recruiter_csv=sample_data/recruiter.csv \
    --projection configs/projections/minimal.json > output.json

# Then, validate
candidate-transformer validate \
    --config configs/projections/minimal.json \
    --input output.json
```
Validation checks that the projected JSON conforms to the schema defined by the projection configuration.

#### Available CLI Commands

| Command    | Description                                      |
|------------|--------------------------------------------------|
| transform  | Ingest, merge and project candidate profiles.     |
| validate   | Validate projected JSON output.                  |

#### Common Options

| Option           | Description                                                                                 |
|------------------|--------------------------------------------------------------------------------------------|
| `--source`       | Specify a data source as `connector=file_path`. Can be repeated for multiple sources.       |
| `--config`, `-c` | Path to pipeline or projection configuration JSON.                                          |
| `--projection`, `-p` | Path to projection configuration JSON (overrides projection in pipeline config).        |
| `--input`        | Input JSON file to validate (used with `validate`).                                         |
| `--help`         | Show CLI help and usage information.                                                        |

**Note:** If `--source` CLI arguments are provided, they will strictly override the `sources` array in your JSON configuration.

### Configurable Projection
The projection layer is entirely runtime-configurable without any code changes. It supports:
- **Field selection**: Output only requested fields.
- **Field remapping**: Support `path` and `from` (e.g., `contact.emails[0]`, `experience[].company`).
- **Runtime Normalization**: Define normalizers directly in JSON (`normalize: "E164"`, `normalize: "canonical"`, `lowercase`, `trim`).
- **Missing Value Policies**: Define `on_missing` as `null`, `omit`, or `error`.

Example usage with `--projection`:
```bash
candidate-transformer transform \
    --source recruiter_csv=sample_data/recruiter.csv \
    --source ats_json=sample_data/ats.json \
    --projection configs/projections/recruiter.json
```

See `configs/projections/` for canonical, recruiter, ats, minimal, and analytics examples.

Configurations dictate how the internal `CanonicalCandidate` is reshaped (projected) into the final JSON output, as well as resolving conflict priorities.
See `configs/default.json` and `configs/minimal.json` for examples.

## Core Features

### Entity Resolution
The framework deterministically merges candidate profiles based on a strict priority cascade, avoiding fragile fuzzy-matching or ML-based heuristics. Records are merged if they share:
1. Exact Phone Match
2. Exact Email Match
3. Exact Name Match (case-insensitive)

### Deterministic Deduplication & ID Generation
- Candidates are assigned a stable `UUIDv5` based on their name and contact information. Identical data yields identical IDs across runs.
- Education and Experience arrays are merged deterministically using composite keys (e.g. `(company, title)` or `(institution, degree, field)`) instead of string equivalence.
- All lists (`emails`, `phones`, `certifications`, `languages`) and `provenance` metadata are sorted deterministically, ensuring perfectly reproducible JSON output.

### Structural Extraction & Normalization
- **Locations**: Mapped to standard ISO-3166 alpha-2 country codes and state/region abbreviations.
- **Links**: Robustly parsed to classify specific URL types (LinkedIn, GitHub, Portfolio) while preserving their full path schema.
- **Projects**: Raw project descriptions are intelligently decomposed into structured `name`, `description`, and `technologies` fields.

### Confidence Scoring
Each resolved candidate receives a rigorous confidence score (0.0 to 1.0) based on:
- **Profile Completeness (Max 0.5)**: Evaluates presence of Name, Contact, Location, Skills, Experience, Education, and Projects.
- **Source Corroboration (Max 0.5)**: Heavily rewards candidates that appear consistently across multiple sources (e.g. found in ATS, Resume, and CSV simultaneously).

### Output Validation
The projected JSON outputs are validated strictly against the dynamic schema defined in your configuration:
- Strongly typed fields (`string`, `number`, `string[]`)
- Strict requirement enforcement
- Deep nesting validation

Use `candidate-transformer validate` to ensure downstream systems receive perfectly formatted data.

## Testing & Quality

To run the exhaustive test suite and quality checks:
```bash
pytest
ruff check .
black --check .
mypy src
```

## Plugin Development
You can register new Connectors, Normalizers, or Strategies dynamically using the registries.
```python
from candidate_transformer.connectors import connector_registry
from candidate_transformer.interfaces.connector import BaseConnector

@connector_registry("my_custom_source")
class CustomConnector(BaseConnector):
    pass
```

