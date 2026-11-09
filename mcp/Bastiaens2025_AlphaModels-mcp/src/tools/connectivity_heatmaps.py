"""Connectivity operations bound to pinned source blocks and shipped table loaders."""
import ast
import contextlib
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Annotated, Literal

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import RendererAgg
import numpy as np
import pandas as pd
import seaborn as sns
from fastmcp import FastMCP
from pydantic import Field

REPO = Path(__file__).resolve().parents[2] / "repo/Bastiaens2025_AlphaModels"
SOURCE = REPO / "code/Connectivity_Heatmaps.py"
REFERENCE = "https://github.com/GriffithsLab/Bastiaens2025_AlphaModels/blob/74f924beb50f60513ccb7efe065dcc1014d0c953/code/Connectivity_Heatmaps.py"
DATA_REFERENCE = "https://github.com/GriffithsLab/Bastiaens2025_AlphaModels/blob/74f924beb50f60513ccb7efe065dcc1014d0c953/data/Connectivity_Heatmap_Data.ipynb"
SOURCE_SHA256 = "b6112e8f85d897e78186a86e8ad0525204f7267b78c508e75ea6d7abc7e6c27d"
connectivity_heatmaps_mcp = FastMCP(name="connectivity_heatmaps")


class _BindInputs(ast.NodeTransformer):
    def __init__(self, inputs):
        self.inputs = inputs

    @staticmethod
    def value(name):
        return ast.parse(f"__inputs__[{name!r}]", mode="eval").body

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in self.inputs:
                node.value = ast.copy_location(self.value(name), node.value)
            elif name == "stop" and "duration_s" in self.inputs:
                # Keep the source delay term and bind its duration literal.
                node.value.left = ast.copy_location(self.value("duration_s"), node.value.left)
        return self.generic_visit(node)

    def visit_Call(self, node):
        self.generic_visit(node)
        function = ast.unparse(node.func)
        if function == "np.random.uniform":
            node.args[:2] = [self.value("noise_low"), self.value("noise_high")]
        elif function == "np.random.seed":
            node.args[0] = self.value("seed")
        elif function == "signal.resample":
            node.args[1] = self.value("resample_samples")
        elif function == "welch":
            for keyword in node.keywords:
                if keyword.arg in ["fs", "nperseg", "noverlap"]:
                    keyword.value = self.value({"fs": "welch_fs_hz", "nperseg": "welch_nperseg", "noverlap": "welch_noverlap"}[keyword.arg])
        elif function == "FOOOF":
            for keyword in node.keywords:
                if keyword.arg in self.inputs:
                    keyword.value = self.value(keyword.arg)
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "fit" and len(node.args) == 3:
            node.args[2] = self.value("fit_range")
        return node

    def visit_Compare(self, node):
        self.generic_visit(node)
        if "min_peak_power" in self.inputs and len(node.ops) == 1 and isinstance(node.ops[0], ast.Gt):
            if isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value == .5:
                node.comparators[0] = self.value("min_peak_power")
        return node


def _grid(values, name):
    result = np.asarray(values, dtype=float)
    if result.ndim != 1 or not len(result) or not np.isfinite(result).all() or len(np.unique(result)) != len(result):
        raise ValueError(f"{name} must be a nonempty finite vector of unique values")
    return result


def _folder(output_dir):
    base = Path(output_dir).expanduser().resolve() if output_dir else Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="bastiaens_connectivity_", dir=base))


def _serialize(table, folder, reference, metadata, figure):
    csv = folder / "heatmap.csv"
    arrays = folder / "heatmap.npz"
    image = folder / "heatmap.png"
    info = folder / "metadata.json"
    table.to_csv(csv, float_format="%.17g")
    rows = table.index.to_numpy()
    columns = table.columns.to_numpy()
    if rows.dtype.kind == "O":
        rows = rows.astype(str)
    if columns.dtype.kind == "O":
        columns = columns.astype(str)
    np.savez_compressed(arrays, dominant_frequency_hz=table.to_numpy(dtype=float), row_labels=rows, column_labels=columns)
    figure.savefig(image, dpi=140, bbox_inches="tight")
    metadata.update({"reference": reference, "shape": list(table.shape), "frequency_units": "Hz",
                     "row_labels": rows.tolist(), "column_labels": columns.tolist()})
    info.write_text(json.dumps(metadata, indent=2) + "\n")
    return {"message": f"Produced connectivity peak-frequency table with shape {table.shape}", "reference": reference,
            "artifacts": [{"description": "Labeled dominant-frequency CSV", "path": str(csv)},
                          {"description": "Native values and axis labels", "path": str(arrays)},
                          {"description": "Connectivity heatmap", "path": str(image)},
                          {"description": "Axis settings and source provenance", "path": str(info)}],
            "shape": list(table.shape), "row_axis": metadata["row_axis"], "column_axis": metadata["column_axis"]}


def _compute(model, inputs, output_dir):
    for name, value in inputs.items():
        if isinstance(value, (int, float)) and not np.isfinite(value):
            raise ValueError(f"{name} must be finite")
    for name in ["dt", "welch_fs_hz", "duration_s"]:
        if inputs[name] <= 0:
            raise ValueError(f"{name} must be positive")
    if inputs["welch_nperseg"] < 2 or not 0 <= inputs["welch_noverlap"] < inputs["welch_nperseg"]:
        raise ValueError("Welch requires nperseg>=2 and 0<=noverlap<nperseg")
    if not 0 < inputs["fit_range"][0] < inputs["fit_range"][1]:
        raise ValueError("Fit frequency bounds must be positive and increasing")
    if not 0 <= inputs["seed"] <= 2**32 - 1:
        raise ValueError("seed must be a NumPy uint32 seed")
    if model == "jr":
        if len(inputs["C3_tot"]) != len(inputs["C4_tot"]):
            raise ValueError("Upstream JR result indexing requires equally sized C3 and C4 grids")
        if inputs["noise_low"] > inputs["noise_high"]:
            raise ValueError("noise_low must be less than or equal to noise_high")
        if not np.isclose(inputs["welch_fs_hz"], 1 / inputs["dt"]):
            raise ValueError("JR welch_fs_hz must equal 1/dt to preserve physical frequency labels")
        if len(np.arange(0, inputs["duration_s"], inputs["dt"])) <= max(2005, 1000 + inputs["welch_noverlap"]):
            raise ValueError("JR duration/dt is too short for upstream flatness/transient sample indices")
    else:
        if inputs["resample_samples"] <= 1000 + inputs["welch_noverlap"]:
            raise ValueError("RRW resampling is too short for the upstream1000-sample transient")
        if not np.isclose(inputs["resample_samples"] / inputs["duration_s"], inputs["welch_fs_hz"]):
            raise ValueError("RRW resample_samples/duration_s must equal welch_fs_hz")
        if inputs["duration_s"] / inputs["dt"] <= 30001:
            raise ValueError("RRW duration/dt is too short for upstream flatness sample indices")
    text = SOURCE.read_text()
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Connectivity source differs from pinned upstream implementation")
    start = text[:text.index("# Jansen-Rit")].count("\n") + 1
    lw = text[:text.index("# Liley-Wright")].count("\n") + 1
    rrw = text[:text.index("# Robinson-Rennie-Wright")].count("\n") + 1
    tail = text[:text.index("rocket_colormap =")].count("\n") + 1
    low, high = (start, lw) if model == "jr" else (rrw, tail)
    original = ast.parse(text, filename=str(SOURCE))
    nodes = [n for n in original.body if n.lineno < start or low <= n.lineno < high]
    bound = _BindInputs(inputs).visit(ast.Module(body=nodes, type_ignores=[]))
    ast.fix_missing_locations(bound)
    namespace = {"__inputs__": inputs, "__name__": "__upstream_binding__", "__file__": str(SOURCE)}
    folder = _folder(output_dir)
    with RendererAgg.lock:
        previous = set(plt.get_fignums())
        random_state = np.random.get_state()
        try:
            np.random.seed(inputs["seed"])
            plt.figure()
            with contextlib.redirect_stdout(sys.stderr):
                exec(compile(bound, str(SOURCE), "exec"), namespace)
            table = namespace["data2" if model == "jr" else "data"]
            settings = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in inputs.items()}
            return _serialize(table, folder, REFERENCE,
                              {"model": model, "settings": settings, "source_sha256": SOURCE_SHA256,
                               "row_axis": "C3/C1" if model == "jr" else "nu_rs (V s)",
                               "column_axis": "C4/C1" if model == "jr" else "nu_sr (V s)",
                               "source_limits": "JR square grids and source sample-index flatness tests retained; RRW source resampling and transient retained."}, plt.gcf())
        finally:
            np.random.set_state(random_state)
            for number in set(plt.get_fignums()) - previous:
                plt.close(number)


@connectivity_heatmaps_mcp.tool()
def connectivity_heatmap_jansen_rit(
    C3_proportions: Annotated[list[float], "C3/C1 grid; must have same length as C4_proportions due to source indexing"],
    C4_proportions: Annotated[list[float], "C4/C1 grid; source returns rows C3 and columns C4"],
    A: Annotated[float, "Excitatory amplitude in mV"] = 3.25,
    B: Annotated[float, "Inhibitory amplitude in mV"] = 22.0,
    C1: Annotated[float, "Excitatory connectivity C1"] = 135.0,
    C2: Annotated[float | None, Field(description="Excitatory connectivity C2; None keeps source0.8*C1")] = None,
    v0: Annotated[float, "Firing threshold in mV"] = 6.0,
    a: Annotated[float, "Excitatory rate constant in s^-1"] = 100.0,
    b: Annotated[float, "Inhibitory rate constant in s^-1"] = 50.0,
    nu_max: Annotated[float, "Maximum half firing rate in s^-1"] = 2.5,
    r: Annotated[float, "Sigmoid slope in mV^-1"] = .56,
    noise_low: Annotated[float, "Uniform external input lower bound in s^-1"] = 120.0,
    noise_high: Annotated[float, "Uniform external input upper bound in s^-1"] = 320.0,
    duration_s: Annotated[float, "Simulation seconds; source flatness checks require at least2006 samples"] = 10.0,
    dt: Annotated[float, "Euler integration step in seconds"] = .001,
    welch_fs_hz: Annotated[float, "Welch sampling frequency; must equal1/dt"] = 1000.0,
    welch_nperseg: Annotated[int, "Welch segment length in samples"] = 1000,
    welch_noverlap: Annotated[int, "Welch overlap in samples"] = 125,
    max_n_peaks: Annotated[int, "Maximum FOOOF fitted peaks"] = 2,
    min_peak_height: Annotated[float, "Minimum FOOOF peak height"] = 1.0,
    aperiodic_mode: Annotated[Literal["fixed", "knee"], "FOOOF aperiodic component mode"] = "knee",
    fit_min_hz: Annotated[float, "FOOOF lower fitting frequency"] = 1.0,
    fit_max_hz: Annotated[float, "FOOOF upper fitting frequency"] = 50.0,
    seed: Annotated[int, "NumPy seed for source uniform input generation"] = 20261106,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Sweep upstream Jansen–Rit connectivity and extract dominant FOOOF peaks.
    Input is equally sized connectivity grids and model settings; output is a labeled table and heatmap.
    """
    values = locals().copy()
    inputs = {k: v for k, v in values.items() if k not in ["C3_proportions", "C4_proportions", "C2", "output_dir", "fit_min_hz", "fit_max_hz"]}
    inputs.update(C3_tot=_grid(C3_proportions, "C3_proportions"), C4_tot=_grid(C4_proportions, "C4_proportions"),
                  stim_time=duration_s, fit_range=[fit_min_hz, fit_max_hz])
    if C2 is not None:
        inputs["C2"] = C2
    return _compute("jr", inputs, output_dir)


@connectivity_heatmaps_mcp.tool()
def connectivity_heatmap_robinson_rennie_wright(
    nu_rs_values: Annotated[list[float], "Relay to reticular coupling grid in V s; output rows"],
    nu_sr_values: Annotated[list[float], "Reticular to relay coupling grid in V s; output columns"],
    nu_ee: Annotated[float, "Cortical recurrent excitatory coupling in V s"] = .00303,
    nu_ei: Annotated[float, "Cortical inhibitory coupling in V s"] = -.006,
    nu_es: Annotated[float, "Relay to cortical coupling in V s"] = .00206,
    nu_se: Annotated[float, "Cortical to relay coupling in V s"] = .00218,
    nu_re: Annotated[float, "Cortical to reticular coupling in V s"] = .00033,
    nu_sn: Annotated[float, "External to relay coupling in V s"] = .00098,
    alpha: Annotated[float, "Slow dendritic rate in s^-1"] = 83.33,
    beta: Annotated[float, "Fast dendritic rate in s^-1"] = 769.23,
    gamma: Annotated[float, "Cortical propagation rate in s^-1"] = 116.0,
    t0: Annotated[float, "Corticothalamic delay in seconds"] = .080,
    Qmax: Annotated[float, "Maximum firing rate in s^-1"] = 340.0,
    theta: Annotated[float, "Firing threshold in volts"] = .01292,
    sigma: Annotated[float, "Threshold spread in volts"] = .0038,
    phin_0: Annotated[float, "Mean external input in s^-1"] = 1.0,
    phin: Annotated[float, "External noise parameter"] = .0005,
    duration_s: Annotated[float, "Nominal simulation seconds, before source half-delay initialization"] = 100.0,
    dt: Annotated[float, "Euler-Maruyama step in seconds"] = .0001,
    resample_samples: Annotated[int, "Output resampling count; divided by duration_s must equal welch_fs_hz"] = 10000,
    welch_fs_hz: Annotated[float, "Welch sampling frequency after resampling"] = 100.0,
    welch_nperseg: Annotated[int, "Welch segment length in samples"] = 1000,
    welch_noverlap: Annotated[int, "Welch overlap in samples"] = 125,
    peak_width_min_hz: Annotated[float, "Minimum FOOOF peak width in Hz"] = 2.0,
    peak_width_max_hz: Annotated[float, "Maximum FOOOF peak width in Hz"] = 8.0,
    aperiodic_mode: Annotated[Literal["fixed", "knee"], "FOOOF aperiodic component mode"] = "knee",
    fit_min_hz: Annotated[float, "FOOOF lower fitting frequency"] = 2.0,
    fit_max_hz: Annotated[float, "FOOOF upper fit bound; source70Hz is trimmed to Nyquist by FOOOF"] = 70.0,
    min_peak_power: Annotated[float, "Source post-fit peak power threshold"] = .5,
    seed: Annotated[int, "Source NumPy noise seed; default0 matches upstream"] = 0,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Sweep upstream RRW relay/reticular connectivity and extract dominant peaks.
    Input is coupling grids and model settings; output is a labeled table and heatmap.
    """
    values = locals().copy()
    omitted = ["nu_rs_values", "nu_sr_values", "output_dir", "fit_min_hz", "fit_max_hz", "peak_width_min_hz", "peak_width_max_hz"]
    inputs = {k: v for k, v in values.items() if k not in omitted}
    if not 0 < peak_width_min_hz < peak_width_max_hz:
        raise ValueError("Peak-width bounds must be positive and increasing")
    inputs.update(nu_rs_tot=_grid(nu_rs_values, "nu_rs_values"), nu_sr_tot=_grid(nu_sr_values, "nu_sr_values"),
                  peak_width_limits=[peak_width_min_hz, peak_width_max_hz], fit_range=[fit_min_hz, fit_max_hz])
    return _compute("rrw", inputs, output_dir)


@connectivity_heatmaps_mcp.tool()
def load_precomputed_connectivity_heatmap(
    model: Annotated[Literal["jansen_rit", "liley_wright", "robinson_rennie_wright"], "Choose one shipped full-resolution paper table"],
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Load the paper's precomputed connectivity result using its notebook loader.
    Input is a model identifier; output is the original labeled table and a heatmap.
    """
    filename = {"jansen_rit": "Jansen_Rit_EI_connection.csv", "liley_wright": "Liley_EI_connection.csv",
                "robinson_rennie_wright": "Robinson_Heatmap_Data.csv"}[model]
    source = REPO / "data" / filename
    # These are the concrete pandas calls in Connectivity_Heatmap_Data.ipynb.
    table = pd.read_csv(source).set_index("nu_rs") if model == "robinson_rennie_wright" else pd.read_csv(source, header=0, index_col=0)
    folder = _folder(output_dir)
    row, column = {"jansen_rit": ("C3/C1", "C4/C1"), "liley_wright": ("N_ei_b", "N_ie_b"),
                   "robinson_rennie_wright": ("nu_rs (V s)", "nu_sr (V s)")}[model]
    with RendererAgg.lock:
        figure, axis = plt.subplots()
        try:
            sns.heatmap(table, ax=axis, vmax=12, cbar_kws={"label": "Dominant frequency (Hz)"})
            axis.set_xlabel(column)
            axis.set_ylabel(row)
            axis.invert_yaxis()
            if model == "robinson_rennie_wright":
                axis.invert_xaxis()
            return _serialize(table, folder, DATA_REFERENCE,
                              {"model": model, "row_axis": row, "column_axis": column, "source_file": filename,
                               "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                               "fixed_data": True, "missing_values_preserved": True}, figure)
        finally:
            plt.close(figure)
