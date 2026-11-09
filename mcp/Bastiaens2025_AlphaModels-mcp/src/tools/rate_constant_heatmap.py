"""Rate-constant sweeps through exact official Bastiaens notebook code cells."""
from __future__ import annotations

import ast
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from typing import Annotated, Literal

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import RendererAgg
import numpy as np
from scipy import signal
from fastmcp import FastMCP
from pydantic import Field

REFERENCE = "https://github.com/GriffithsLab/Bastiaens2025_AlphaModels/blob/74f924beb50f60513ccb7efe065dcc1014d0c953/notebooks/Rate_Constant_Heatmap.ipynb"
SOURCE = Path(__file__).resolve().parents[2] / "repo/Bastiaens2025_AlphaModels/notebooks/Rate_Constant_Heatmap.ipynb"
rate_constant_heatmap_mcp = FastMCP(name="rate_constant_heatmap")


def _run(model: str, parameters: dict, settings: dict, output_dir: str | None) -> dict:
    grids = [parameters[name] for name in ("tau_ee", "tau_ii") if name in parameters] if model == "LW" else [parameters["tau_e"], parameters["tau_i"]]
    if any(not grid or not np.isfinite(grid).all() or min(grid) <= 0 for grid in grids):
        raise ValueError("Time-constant grids must be nonempty, finite, and positive")
    if not all(np.isfinite(np.asarray(value)).all() for value in parameters.values()):
        raise ValueError("Model parameters must be finite")
    duration = settings["duration"]
    dt = settings["dt"]
    if not np.isfinite(duration) or not np.isfinite(dt) or duration <= 0 or dt <= 0:
        raise ValueError("Duration and dt must be positive and finite")
    minimum_samples = 20006 if model == "JR" else 2007
    if int(duration / dt) < minimum_samples:
        raise ValueError(f"Source {model} transient checks require at least {minimum_samples} simulation samples")
    if settings["welch_noverlap"] < 0 or settings["welch_nperseg"] <= settings["welch_noverlap"]:
        raise ValueError("Welch nperseg must exceed nonnegative noverlap")
    if settings["welch_fs"] <= 0 or settings["fit_freq_range"][0] <= 0 or settings["fit_freq_range"][0] >= settings["fit_freq_range"][1]:
        raise ValueError("Welch sampling rate and increasing fit frequency bounds must be positive")
    # The upstream resampling convention uses nominal simulation duration,
    # retaining its fixed initial-sample removal before resampling.
    if not np.isclose(settings["resample_count"] / duration, settings["welch_fs"]):
        raise ValueError("resample_count / duration must equal welch_fs under the source nominal-duration convention")
    base = Path(output_dir).expanduser().resolve() if output_dir else Path.cwd() / "outputs"
    base.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix="rate_" + model.lower() + "_", dir=base))
    notebook = json.loads(SOURCE.read_text())
    indices = {"JR": [0, 2, 3, 4], "LW": [0, 11, 12, 13, 14]}[model]
    bindings = {**parameters, "stim_time": duration, "sim_time": duration, "dt": dt}
    namespace = {"__name__": "__upstream_rate_sweep__", "signal": signal}
    with RendererAgg.lock:
        prior_figures = set(plt.get_fignums())
        prior_random_state = np.random.get_state() if settings["seed"] is not None else None
        if settings["seed"] is not None:
            np.random.seed(settings["seed"])
        try:
            for index in indices:
                tree = ast.parse("".join(notebook["cells"][index]["source"]))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                        name = node.targets[0].id
                        if name in bindings:
                            value = bindings[name]
                            expression = "np.array(" + repr(value) + ")" if isinstance(value, list) else repr(value)
                            node.value = ast.parse(expression, mode="eval").body
                    if not isinstance(node, ast.Call):
                        continue
                    if isinstance(node.func, ast.Name) and node.func.id == "welch":
                        for keyword in node.keywords:
                            if keyword.arg in ("fs", "nperseg", "noverlap"):
                                keyword.value = ast.Constant(settings["welch_" + keyword.arg])
                    elif isinstance(node.func, ast.Name) and node.func.id == "FOOOF":
                        for keyword in node.keywords:
                            if keyword.arg in ("max_n_peaks", "min_peak_height", "aperiodic_mode"):
                                keyword.value = ast.Constant(settings[keyword.arg])
                        node.keywords.append(ast.keyword(arg="verbose", value=ast.Constant(False)))
                    elif isinstance(node.func, ast.Attribute) and node.func.attr == "fit" and isinstance(node.func.value, ast.Name) and node.func.value.id == "fm":
                        node.args[2] = ast.parse(repr(list(settings["fit_freq_range"])), mode="eval").body
                    elif isinstance(node.func, ast.Attribute) and node.func.attr == "resample":
                        node.args[1] = ast.Constant(settings["resample_count"])
                    elif isinstance(node.func, ast.Attribute) and node.func.attr == "uniform" and model == "JR":
                        node.args[0] = ast.Constant(settings["noise_low"])
                        node.args[1] = ast.Constant(settings["noise_high"])
                ast.fix_missing_locations(tree)
                # Native FOOOF diagnostics belong on stderr/logs, never protocol stdout.
                with redirect_stdout(io.StringIO()):
                    exec(compile(tree, str(SOURCE) + f":cell{index}", "exec"), namespace)
            data = namespace["data"]
            data.to_csv(destination / "peak_frequency.csv")
            np.savez(destination / "peak_frequency.npz", peak_frequency=data.to_numpy(), tau_i=data.index.to_numpy(), tau_e=data.columns.to_numpy())
            plt.gcf().savefig(destination / "heatmap.png", dpi=150, bbox_inches="tight")
        finally:
            if prior_random_state is not None:
                np.random.set_state(prior_random_state)
            for number in set(plt.get_fignums()) - prior_figures:
                plt.close(number)
    return {"message": "Source rate-constant sweep and dominant FOOOF peak extraction completed.", "reference": REFERENCE,
            "artifacts": [{"description": text, "path": str(destination / filename)} for filename, text in [
                ("peak_frequency.npz", "Native peak-frequency matrix and time-constant axes in ms"),
                ("peak_frequency.csv", "Labeled dominant-frequency table in Hz"), ("heatmap.png", "Source heatmap figure")]],
            "model": model, "shape": list(data.shape), "duration_seconds": duration, "dt_seconds": dt,
            "zero_meaning": "Source did not select a spectral peak", "seed": settings["seed"]}


@rate_constant_heatmap_mcp.tool()
def rate_constant_heatmap_jansen_rit(
    tau_e_range: Annotated[list[float], "Positive synaptic time-constant grid in ms."],
    tau_i_range: Annotated[list[float], "Positive synaptic time-constant grid in ms."],
    A: Annotated[float, 'Source JR parameter A; units and default follow the official notebook.'] = 3.25,
    B: Annotated[float, 'Source JR parameter B; units and default follow the official notebook.'] = 22.0,
    C1: Annotated[float, 'Source JR parameter C1; units and default follow the official notebook.'] = 135.0,
    C2: Annotated[float | None, Field(description='Optional excitatory connectivity C2 override; null retains the source 0.8*C1 expression.')] = None,
    C3: Annotated[float | None, Field(description='Optional pyramidal-to-inhibitory C3 override; null retains the source 0.25*C1 expression.')] = None,
    C4: Annotated[float | None, Field(description='Optional inhibitory connectivity C4 override; null retains the source 0.25*C1 expression.')] = None,
    v0: Annotated[float, 'Source JR parameter v0; units and default follow the official notebook.'] = 6.0,
    nu_max: Annotated[float, 'Source JR parameter nu_max; units and default follow the official notebook.'] = 2.5,
    r: Annotated[float, 'Source JR parameter r; units and default follow the official notebook.'] = 0.56,
    duration: Annotated[float, "Nominal simulation duration in seconds; resampling controls must stay consistent."] = 100.0,
    dt: Annotated[float, "Simulation step in seconds."] = 0.0001,
    resample_count: Annotated[int, "Number of resampled points; divided by duration must equal welch_fs."] = 10000,
    welch_fs: Annotated[float, "Source Welch sampling rate in Hz."] = 100.0,
    welch_nperseg: Annotated[int, "Welch segment sample count."] = 1000,
    welch_noverlap: Annotated[int, "Welch segment overlap in samples."] = 125,
    max_n_peaks: Annotated[int, "Maximum number of FOOOF peaks per grid point."] = 2,
    min_peak_height: Annotated[float, "FOOOF minimum peak height in log10 power."] = 1.0,
    aperiodic_mode: Annotated[Literal["fixed", "knee"], "FOOOF aperiodic fit parameterization."] = "knee",
    fit_freq_range: Annotated[tuple[float, float], "FOOOF lower and upper fit frequencies in Hz."] = (1.0, 50.0),
    noise_low: Annotated[float, "Lower source uniform input-drive bound in s^-1."] = 120.0,
    noise_high: Annotated[float, "Upper source uniform input-drive bound in s^-1."] = 320.0,
    seed: Annotated[int | None, Field(description="NumPy random seed; null retains the source current random stream.")] = None,
    output_dir: Annotated[str | None, Field(description="Output base directory; each call creates a fresh subdirectory.")] = None,
) -> dict:
    """Sweep jansen rit synaptic time constants and extract dominant spectral peaks.
    Time-constant grids and source parameters → labeled peak-frequency matrix and scientific heatmap.
    """
    parameters = {'tau_e': tau_e_range, 'tau_i': tau_i_range, 'A': A, 'B': B, 'C1': C1, 'C2': C2, 'C3': C3, 'C4': C4, 'v0': v0, 'nu_max': nu_max, 'r': r}
    settings = {'duration': duration, 'dt': dt, 'welch_fs': welch_fs, 'welch_nperseg': welch_nperseg, 'welch_noverlap': welch_noverlap, 'max_n_peaks': max_n_peaks, 'min_peak_height': min_peak_height, 'aperiodic_mode': aperiodic_mode, 'fit_freq_range': fit_freq_range, 'seed': seed, 'resample_count': resample_count, "noise_low": noise_low, "noise_high": noise_high}
    parameters = {name: value for name, value in parameters.items() if value is not None}
    return _run('JR', parameters, settings, output_dir)


@rate_constant_heatmap_mcp.tool()
def rate_constant_heatmap_liley_wright(
    tau_ee_range: Annotated[list[float], "Positive synaptic time-constant grid in ms."],
    tau_ii_range: Annotated[list[float], "Positive synaptic time-constant grid in ms."],
    S_e_max: Annotated[float, 'Source LW parameter S_e_max; units and default follow the official notebook.'] = 0.5,
    S_i_max: Annotated[float, 'Source LW parameter S_i_max; units and default follow the official notebook.'] = 0.5,
    sigma_e: Annotated[float, 'Source LW parameter sigma_e; units and default follow the official notebook.'] = 5.0,
    sigma_i: Annotated[float, 'Source LW parameter sigma_i; units and default follow the official notebook.'] = 5.0,
    tau_e: Annotated[float, 'Source LW parameter tau_e; units and default follow the official notebook.'] = 94.0,
    tau_i: Annotated[float, 'Source LW parameter tau_i; units and default follow the official notebook.'] = 42.0,
    h_ee_eq: Annotated[float, 'Source LW parameter h_ee_eq; units and default follow the official notebook.'] = 4.0,
    h_ei_eq: Annotated[float, 'Source LW parameter h_ei_eq; units and default follow the official notebook.'] = 45.0,
    Gamma_ee: Annotated[float, 'Source LW parameter Gamma_ee; units and default follow the official notebook.'] = 0.71,
    Gamma_ei: Annotated[float, 'Source LW parameter Gamma_ei; units and default follow the official notebook.'] = 0.71,
    Gamma_ie: Annotated[float, 'Source LW parameter Gamma_ie; units and default follow the official notebook.'] = 0.71,
    Gamma_ii: Annotated[float, 'Source LW parameter Gamma_ii; units and default follow the official notebook.'] = 0.71,
    p_ee: Annotated[float, 'Source LW parameter p_ee; units and default follow the official notebook.'] = 3.46,
    p_ee_sd: Annotated[float, 'Source LW parameter p_ee_sd; units and default follow the official notebook.'] = 1.0,
    p_ei: Annotated[float, 'Source LW parameter p_ei; units and default follow the official notebook.'] = 5.07,
    N_ei_b: Annotated[float, 'Source LW parameter N_ei_b; units and default follow the official notebook.'] = 3000.0,
    N_ee_b: Annotated[float, 'Source LW parameter N_ee_b; units and default follow the official notebook.'] = 3000.0,
    N_ie_b: Annotated[float, 'Source LW parameter N_ie_b; units and default follow the official notebook.'] = 500.0,
    N_ii_b: Annotated[float, 'Source LW parameter N_ii_b; units and default follow the official notebook.'] = 500.0,
    duration: Annotated[float, "Nominal simulation duration in seconds; resampling controls must stay consistent."] = 50.0,
    dt: Annotated[float, "Simulation step in seconds."] = 0.0001,
    resample_count: Annotated[int, "Number of resampled points; divided by duration must equal welch_fs."] = 5000,
    welch_fs: Annotated[float, "Source Welch sampling rate in Hz."] = 100.0,
    welch_nperseg: Annotated[int, "Welch segment sample count."] = 1000,
    welch_noverlap: Annotated[int, "Welch segment overlap in samples."] = 125,
    max_n_peaks: Annotated[int, "Maximum number of FOOOF peaks per grid point."] = 2,
    min_peak_height: Annotated[float, "FOOOF minimum peak height in log10 power."] = 1.0,
    aperiodic_mode: Annotated[Literal["fixed", "knee"], "FOOOF aperiodic fit parameterization."] = "knee",
    fit_freq_range: Annotated[tuple[float, float], "FOOOF lower and upper fit frequencies in Hz."] = (1.0, 50.0),
    seed: Annotated[int | None, Field(description="NumPy random seed; null retains the source current random stream.")] = None,
    output_dir: Annotated[str | None, Field(description="Output base directory; each call creates a fresh subdirectory.")] = None,
) -> dict:
    """Sweep liley wright synaptic time constants and extract dominant spectral peaks.
    Time-constant grids and source parameters → labeled peak-frequency matrix and scientific heatmap.
    """
    parameters = {'tau_ee': tau_ee_range, 'tau_ii': tau_ii_range, 'S_e_max': S_e_max, 'S_i_max': S_i_max, 'sigma_e': sigma_e, 'sigma_i': sigma_i, 'tau_e': tau_e, 'tau_i': tau_i, 'h_ee_eq': h_ee_eq, 'h_ei_eq': h_ei_eq, 'Gamma_ee': Gamma_ee, 'Gamma_ei': Gamma_ei, 'Gamma_ie': Gamma_ie, 'Gamma_ii': Gamma_ii, 'p_ee': p_ee, 'p_ee_sd': p_ee_sd, 'p_ei': p_ei, 'N_ei_b': N_ei_b, 'N_ee_b': N_ee_b, 'N_ie_b': N_ie_b, 'N_ii_b': N_ii_b}
    settings = {'duration': duration, 'dt': dt, 'welch_fs': welch_fs, 'welch_nperseg': welch_nperseg, 'welch_noverlap': welch_noverlap, 'max_n_peaks': max_n_peaks, 'min_peak_height': min_peak_height, 'aperiodic_mode': aperiodic_mode, 'fit_freq_range': fit_freq_range, 'seed': seed, 'resample_count': resample_count}
    return _run('LW', parameters, settings, output_dir)


