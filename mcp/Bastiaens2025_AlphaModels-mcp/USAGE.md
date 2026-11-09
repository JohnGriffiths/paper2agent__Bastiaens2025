# Bastiaens alpha-model MCP server

This package exposes the research code for **A comprehensive investigation of intracortical and corticothalamic models of the alpha rhythm** as 25 local MCP tools. It uses the Jansen–Rit (JR), Moran–David–Friston (MDF), Liley–Wright (LW), and Robinson–Rennie–Wright (RRW) implementations from [Bastiaens2025_AlphaModels](https://github.com/GriffithsLab/Bastiaens2025_AlphaModels), pinned at commit `74f924beb50f60513ccb7efe065dcc1014d0c953`.

## Install and start

Extract `Bastiaens2025_AlphaModels-mcp.zip`. Run the following commands inside its `Bastiaens2025_AlphaModels-mcp` directory:

```bash
python3.10 -m venv .venv
.venv/bin/python -m pip install -r src/requirements.txt
.venv/bin/python -m pip check
.venv/bin/python src/Bastiaens2025_AlphaModels_mcp.py
```

The last command starts the stdio server and waits for an MCP client. Keep the `src/` and `repo/` directories together: wrappers load the included pinned research code and data using package-relative paths. The scientific source is included directly; it does not require a separate Git checkout or research-package installation.

Python 3.10 and a CPU are required. No GPU, credentials, remote model service, or external scientific dataset is needed for the built-in simulations and shipped-table retrieval. Installation needs access to the packages pinned in `src/requirements.txt`. Scientific outputs require a writable directory. Simulation and fitting costs grow with duration, integration resolution, and sweep size; start with one or two grid values.

The runtime pins FastMCP 4.0.3, NumPy 1.23.5, SciPy 1.9.1, Matplotlib 3.5.0, pandas 2.0.1, seaborn 0.12.2, FOOOF 1.1.0, and Shapely 2.0.4, together with the resolved dependency closure in `src/requirements.txt`.

For a client that accepts MCP JSON configuration, replace both example paths with absolute paths on the recipient machine:

```json
{
  "mcpServers": {
    "bastiaens-alpha-models": {
      "command": "/absolute/path/Bastiaens2025_AlphaModels-mcp/.venv/bin/python",
      "args": ["/absolute/path/Bastiaens2025_AlphaModels-mcp/src/Bastiaens2025_AlphaModels_mcp.py"]
    }
  }
}
```

Optional Claude Code registration uses the installed FastMCP 4.0.3 command syntax:

```bash
.venv/bin/fastmcp install claude-code src/Bastiaens2025_AlphaModels_mcp.py \
  --name bastiaens-alpha-models --python 3.10 \
  --with-requirements src/requirements.txt --project "$PWD"
```

The flags were checked with the installed `fastmcp install claude-code --help`. Client registration is a separate user action and was not performed during delivery.

## Tools

All names below are exposed without module prefixes. The MCP schemas provide the scientific parameter descriptions, units, defaults, and required inputs.

| Operation | Exposed tool names |
| --- | --- |
| Time series and Welch spectra | `simulate_jansen_rit_time_series`, `simulate_moran_david_friston_time_series`, `simulate_liley_wright_time_series`, `simulate_robinson_rennie_wright_time_series` |
| Analytical spectra | `analytical_power_spectrum_jansen_rit`, `analytical_power_spectrum_moran_david_friston`, `analytical_power_spectrum_liley_wright`, `analytical_power_spectrum_robinson_rennie_wright` |
| Synaptic time-constant sweeps | `rate_constant_heatmap_jansen_rit`, `rate_constant_heatmap_liley_wright` |
| Connectivity sweeps and paper tables | `connectivity_heatmap_jansen_rit`, `connectivity_heatmap_robinson_rennie_wright`, `load_precomputed_connectivity_heatmap` |
| Fixed points and stability | `jansen_rit_fixed_points_stability`, `liley_wright_fixed_points_stability` |
| Firing-rate curves | `sigmoid_response_curve_jansen_rit`, `sigmoid_response_curve_moran_david_friston`, `sigmoid_response_curve_liley_wright`, `sigmoid_response_curve_robinson_rennie_wright` |
| Impulse responses | `impulse_response_curve_jansen_rit`, `impulse_response_curve_moran_david_friston`, `impulse_response_curve_liley_wright`, `impulse_response_curve_robinson_rennie_wright` |
| Aperiodic spectral fits | `estimate_1f_slope_linear_fit`, `estimate_1f_fooof` |

Every successful call returns a JSON object with `message`, `reference`, and an `artifacts` list containing descriptions and absolute file paths. Numerical arrays, labeled tables, figures, and provenance are saved to those paths. Each call creates a fresh subdirectory inside `output_dir`. When it is omitted, analytical, curve, and connectivity tools use the system temporary directory; other tools use `outputs/` in the server's working directory. Repeated calls do not overwrite earlier results. Retain or copy temporary artifacts if you need them beyond the host's temporary-file lifetime.

## First calls

An inexpensive first call retrieves the paper's full-resolution JR connectivity table:

```json
{
  "model": "jansen_rit",
  "output_dir": "/absolute/path/to/results"
}
```

Use that object as arguments to `load_precomputed_connectivity_heatmap`. The other model choices are `liley_wright` and `robinson_rennie_wright`. This operation reads the shipped results; it does not rerun a sweep.

To make the same request programmatically, run this from the extracted package with its `.venv/bin/python` interpreter:

```python
import asyncio
from pathlib import Path
import sys
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

async def main():
    package = Path.cwd().resolve()
    transport = PythonStdioTransport(
        package / "src/Bastiaens2025_AlphaModels_mcp.py",
        python_cmd=sys.executable,
        cwd=str(package),
    )
    async with Client(transport) as client:
        result = await client.call_tool(
            "load_precomputed_connectivity_heatmap",
            {"model": "jansen_rit", "output_dir": str(package / "results")},
        )
        print(result.data)

asyncio.run(main())
```

For a new numerical simulation, call `simulate_jansen_rit_time_series` with:

```json
{
  "duration_seconds": 20.0,
  "dt_seconds": 0.0001,
  "seed": 42,
  "noise_low": 120.0,
  "noise_high": 320.0,
  "output_dir": "/absolute/path/to/results"
}
```

Source-supported scalar parameters can be changed through the tool schema. JR eyes-open drive uses bounds 500–700 instead of 120–320. LW and RRW use their own source parameter sets and units; changing JR noise bounds is not a general four-model eyes-open preset. RRW time-domain simulations must exceed the source's ten-second burn-in.

Required sweep grids are explicit. A small JR connectivity request is:

```json
{
  "C3_proportions": [0.12, 0.13],
  "C4_proportions": [0.50, 0.52],
  "seed": 20261106,
  "output_dir": "/absolute/path/to/results"
}
```

Pass this to `connectivity_heatmap_jansen_rit`. The two grid lengths must match because the upstream result indexing is transposed. RRW connectivity accepts separate `nu_rs_values` and `nu_sr_values` arrays, in V s. Rate-constant sweeps accept positive millisecond grids: JR uses `tau_e_range` and `tau_i_range`; LW uses `tau_ee_range` and `tau_ii_range`.

When changing duration or sampling settings in sweep tools, keep the explicit Welch and resampling settings consistent with the schema. Inconsistent physical sampling rates are rejected. The tools retain the source's sample-index transient and flatness tests; changing an integration step also changes the physical times represented by those fixed indices.

## Array inputs and composition

Analytical-spectrum tools accept an optional `frequency_path`: a JSON numeric array, a JSON object with `frequency_hz`, or an NPZ containing `frequency_hz`. Frequencies must be finite, positive, and strictly increasing. Omitting the path uses the upstream 200-point grid from 1 to 60 Hz. Their `spectrum.npz` contains `frequency_hz` and `power`.

The analytical JR tool exposes `C1`–`C4` as independent numeric arguments: changing `C1` alone retains the explicit defaults of `C2`–`C4`. The JR rate-sweep tool instead uses nullable `C2`–`C4` overrides; omitting them retains the original notebook's expressions derived from `C1`. Consult each tool's schema when composing parameter changes.

Curve tools accept optional JSON/NPZ vector files. Sigmoids use the `voltage` key; JR and LW voltages are mV and RRW voltages are V. MDF units are ambiguous in the source: parameter comments say `na`, while the shared plot labels input mV and response s⁻¹. Its tool preserves numerical values without conversion and records that ambiguity. Impulse responses use `time_seconds`. Bare JSON arrays are also accepted. Omitted paths retain the source demonstration grids. Threshold and rate sweeps remain explicit scalar arrays in the tool arguments. JR, MDF, and LW excitatory and inhibitory rate arrays are paired and must have equal lengths. RRW sweeps `alpha_values` against a scalar `beta`; each alpha must differ from beta.

The two 1/f tools require an NPZ spectrum file. Select its arrays with `frequency_key` and `power_key`; defaults are `freqs` and `psd`. To fit an analytical-spectrum output, use `frequency_key: "frequency_hz"` and `power_key: "power"`. Read the array names in each artifact rather than relying on artifact-list ordering across different tools.

`estimate_1f_fooof` also requires `fit_freq_range`, for example `[1.0, 50.0]`. `estimate_1f_slope_linear_fit` requires all three Python-style index windows: `pre_peak_index_range`, `post_peak_index_range`, and `full_range`. Each is `[start, stop]`; `null` stop selects the end. Choose windows for the input spectrum's own frequency resolution and peak location. These windows are indices, not Hz. Nonpositive frequencies and powers cannot be used in logarithmic fits; select the fitting ranges accordingly.

All data paths refer to the server's filesystem. Use absolute paths when the client and server have different working directories. Large arrays are returned as files, not embedded in MCP responses.

## Source limitations and validation scope

Two selected operations are excluded because their pinned upstream implementations cannot support a faithful standalone scientific tool:

- `connectivity_heatmap_liley_wright`: the extended LW dynamics reference additional parameters that the repository never defines. The canonical LW simulation is a different source model variant and is not substituted. The shipped precomputed LW connectivity result remains available through the loader.
- `rate_constant_heatmap_moran_david_friston`: both the native script and official notebook test a stale `out` variable before assigning the MDF output. In whole-notebook execution the variable comes from another model or a previous grid point; isolated execution fails. No replacement flatness rule or unrelated-model prerequisite is introduced.

The eyes-open/eyes-closed reference needed `sigr`, `sigma_r`, and a complete `S_i` helper from the pinned canonical time-series source. Those exact cross-file bindings are recorded in development evidence; missing helper definitions were not filled with invented model parameters. The LW rate-sweep tool follows the official notebook's documented parameter values, which differ from the script in some fields.

Scientific validation compares selected operations with retained upstream executions, exercises changed inputs and errors, and checks generated artifacts. Sweep checks use reduced grids; delivery does not claim reproduction of every full-resolution paper sweep or correctness of the entire upstream repository. Runtime validation additionally checks the real stdio inventory and calls in the project runtime, a fresh runtime, and an extracted package at a new location. Detailed execution, independent verification, exclusions, and installation reports are retained outside this runtime archive in the conversion workspace.

The reviewed paper reading skill is a separate component of the combined `bastiaens2025-agent` delivery. Its dense equations and main Table 2 are image assets, and its source inconsistencies are preserved and documented.
