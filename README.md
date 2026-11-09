# Paper2Agent: Bastiaens2025 alpha models

A reviewed paper reading skill and 25 local scientific MCP tools for
[Bastiaens, Momi and Griffiths (2025)](https://doi.org/10.1371/journal.pcbi.1012926).
Use either component independently, or use both to connect paper questions with
numerical experiments. The models are Jansen–Rit, Moran–David–Friston,
Liley–Wright, and Robinson–Rennie–Wright.

| Use case | Start here |
| --- | --- |
| Read the paper, supplements, figures, or parameter tables | [Paper skill](skill/bastiaens2025-alpha-models-paper/SKILL.md) and [reading index](skill/bastiaens2025-alpha-models-paper/references/index.md) |
| Simulate signals, compare spectra, inspect stability, or run sweeps | [MCP tools and input contracts](mcp/Bastiaens2025_AlphaModels-mcp/USAGE.md) |
| Call the tools from Python without an AI assistant | Complete Python client example in the [usage guide](mcp/Bastiaens2025_AlphaModels-mcp/USAGE.md#first-calls) |
| Download a packaged MCP runtime | [GitHub releases](https://github.com/JohnGriffiths/paper2agent__Bastiaens2025/releases) |

GitHub distributes the files. Each user runs their own local Python environment
and MCP server. This repository does not require a shared hosted service.

## Get the repository

```bash
git clone https://github.com/JohnGriffiths/paper2agent__Bastiaens2025.git
cd paper2agent__Bastiaens2025
python3.10 scripts/check_integrity.py
```

For reproducible analyses, record the release and the commit returned by
`git rev-parse HEAD`. To update an existing checkout, use `git pull --ff-only`,
then check the release notes and reinstall requirements if they changed.

## Use the paper skill

Give a filesystem-capable assistant this instruction from the repository root:

> Read `skill/bastiaens2025-alpha-models-paper/SKILL.md`, then explain how the
> paper distinguishes noise-driven alpha from self-sustained oscillations.
> Cite the relevant sections and figures.

No Python installation is needed to read the Markdown, CSVs, or images. The skill
and its assets stay together when moved into an assistant's skill directory.
Dense equations and main Table 2 remain images, and source inconsistencies are
preserved and documented.

## Install the scientific tools

Python 3.10 and a CPU are required. Run these commands from the repository root:

```bash
mcp_dir="$PWD/mcp/Bastiaens2025_AlphaModels-mcp"
python3.10 -m venv "$mcp_dir/.venv"
"$mcp_dir/.venv/bin/python" -m pip install -r "$mcp_dir/src/requirements.txt"
"$mcp_dir/.venv/bin/python" -m pip check
```

Each collaborator creates their own environment. Installed environments and
generated outputs are excluded from Git. The included pinned source and data
do not require another repository checkout, a GPU, or credentials. Installation
requires access to the pinned Python distributions and outputs need a writable
directory. Runtime installation was verified on Linux x86_64 with Python 3.10.15.

## Connect an MCP client

Configure the client to launch the installed Python interpreter and server script.
For clients accepting MCP JSON configuration, replace the example paths below
with the absolute paths to your checkout:

```json
{
  "mcpServers": {
    "bastiaens-alpha-models": {
      "command": "/absolute/path/paper2agent__Bastiaens2025/mcp/Bastiaens2025_AlphaModels-mcp/.venv/bin/python",
      "args": ["/absolute/path/paper2agent__Bastiaens2025/mcp/Bastiaens2025_AlphaModels-mcp/src/Bastiaens2025_AlphaModels_mcp.py"]
    }
  }
}
```

For Claude Code, after setting `mcp_dir` as above, register it for this repository:

```bash
"$mcp_dir/.venv/bin/fastmcp" install claude-code \
  "$mcp_dir/src/Bastiaens2025_AlphaModels_mcp.py" \
  --name bastiaens-alpha-models --python 3.10 \
  --with-requirements "$mcp_dir/src/requirements.txt" --project "$PWD"
```

Restart or reconnect the client after registration. A stdio client starts the
server as needed; running the server by itself waits for a client connection.
The MCP component's [usage guide](mcp/Bastiaens2025_AlphaModels-mcp/USAGE.md)
contains the complete inventory, JSON inputs, Python example, units, and artifact keys.

Suggested first prompts once connected:

- "Load the paper's precomputed Liley–Wright connectivity heatmap."
- "Simulate 20 seconds of Jansen–Rit activity with seed 42 and plot its spectrum."
- "Compare the four default analytical power spectra."

Tools return paths to numerical arrays, tables, figures, and provenance files.
Use an explicit absolute `output_dir` when saving results for an analysis.

## Validation and scientific limits

The delivered runtime passed independent installation and real stdio calls after
extraction at a new path containing spaces: **442 scientific tests**, **124 MCP
acceptance cases**, all **25 tool schemas**, and native numerical/metadata/figure
comparisons for all **67 successful call artifact sets**. These counts describe
the recorded release validation; the lightweight checksum script does not rerun
that scientific suite. The [validation summary](validation/summary.json) records
the tested artifact identity and scope.

The original scientific source is pinned at
`74f924beb50f60513ccb7efe065dcc1014d0c953`; original source files are unchanged.
Two computations remain excluded because of upstream defects: extended LW
connectivity computation and the MDF rate-constant sweep. The shipped precomputed
LW connectivity table remains available. Sweep validation uses reduced grids,
not every full-resolution paper sweep. MDF sigmoid units are ambiguous in the
source and are reported without an invented conversion. Read the
[full limitations](mcp/Bastiaens2025_AlphaModels-mcp/USAGE.md#source-limitations-and-validation-scope)
before interpreting results.

## Citation, licensing, and releases

Cite the [original paper](https://doi.org/10.1371/journal.pcbi.1012926) and record
the repository commit or release used. Machine-readable citation metadata is in
[CITATION.cff](CITATION.cff). Code and paper material have distinct license scopes:
see [LICENSE](LICENSE) and [source attribution](THIRD_PARTY_NOTICES.md).

Versioned releases provide download points for collaborators. The MCP release ZIP
is the independently tested archive, with its checksum recorded in
[validation/summary.json](validation/summary.json). Instructions for maintaining
releases and optional DOI archiving are in [RELEASING.md](RELEASING.md).
