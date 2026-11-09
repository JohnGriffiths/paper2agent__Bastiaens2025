"""Curve tools calling exact function definitions from the pinned research script."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from typing import Annotated, Literal

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import RendererAgg
import numpy as np
from fastmcp import FastMCP
from pydantic import Field

REFERENCE = "https://github.com/GriffithsLab/Bastiaens2025_AlphaModels/blob/74f924beb50f60513ccb7efe065dcc1014d0c953/code/Sigmoid_and_Impulse_Response.py"
SOURCE = Path(__file__).resolve().parents[2] / "repo/Bastiaens2025_AlphaModels/code/Sigmoid_and_Impulse_Response.py"
SOURCE_SHA256 = "adaedaefed9f191e852381aded9b2bcbcd1077dda2035638c3b65fa3aaccfd2e"
sigmoid_and_impulse_response_mcp = FastMCP(name="sigmoid_and_impulse_response")


def _helpers(parameters):
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Upstream curve source differs from the pinned implementation")
    tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) or
             isinstance(n, ast.Import) and any(x.name == "math" for x in n.names)]
    namespace = dict(parameters)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace


def _vector(path, key, default):
    if path is None:
        values = default
    else:
        path = Path(path).expanduser().resolve(strict=True)
        if path.suffix.lower() == ".npz":
            with np.load(path, allow_pickle=False) as data:
                if key not in data:
                    raise ValueError(f"Input NPZ requires a {key} array")
                values = data[key]
        elif path.suffix.lower() == ".json":
            data = json.loads(path.read_text())
            values = data[key] if isinstance(data, dict) else data
        else:
            raise ValueError("Input vector must be JSON or NPZ")
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("Input grid must be a nonempty finite one-dimensional vector")
    return values


def _numbers(values, name, positive=False):
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or not len(array) or not np.isfinite(array).all() or positive and np.any(array <= 0):
        raise ValueError(f"{name} must be a nonempty finite vector" + (" of positive values" if positive else ""))
    return array


def _save(model, kind, grid, curves, settings, output_dir):
    if any(not np.isfinite(value).all() for value in curves.values()):
        raise ValueError("Upstream function returned a nonfinite curve")
    base = Path(output_dir).expanduser().resolve() if output_dir else Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix=f"bastiaens_{kind}_{model}_", dir=base))
    arrays = folder / "curves.npz"
    grid_name = "voltage" if kind == "sigmoid" else "time_seconds"
    np.savez_compressed(arrays, **{grid_name: grid}, **curves)
    figure_path = folder / "curves.png"
    with RendererAgg.lock:
        figure, axes = plt.subplots(1, len(curves), figsize=(5 * len(curves), 3.5), squeeze=False)
        try:
            for axis, (name, values) in zip(axes[0], curves.items()):
                for i, row in enumerate(values):
                    axis.plot(grid if kind == "sigmoid" else grid * 1000, row,
                              label=str(settings["thresholds"][i] if kind == "sigmoid" else settings["rates"][name][i]))
                axis.set_xlabel(settings["voltage_units"] if kind == "sigmoid" else "Time (ms)")
                axis.set_ylabel(settings["response_units"] if kind == "sigmoid" else "mV")
                axis.set_title(f"{model.upper()} {name}")
                axis.grid(True)
                axis.legend(title="Threshold" if kind == "sigmoid" else "Rate (s^-1)")
            figure.tight_layout()
            figure.savefig(figure_path, dpi=160)
        finally:
            plt.close(figure)
    metadata = folder / "metadata.json"
    metadata.write_text(json.dumps({"source": REFERENCE, "source_sha256": SOURCE_SHA256,
                                    "model": model, "kind": kind, "settings": settings}, indent=2) + "\n")
    return {"message": f"Evaluated upstream {model} {kind} curves", "reference": REFERENCE,
            "artifacts": [{"description": "Input grid and curve arrays", "path": str(arrays)},
                          {"description": "Model curve figure", "path": str(figure_path)},
                          {"description": "Scientific settings and provenance", "path": str(metadata)}],
            "model": model, "num_samples": len(grid), "shapes": {k: list(v.shape) for k, v in curves.items()}}


def _sigmoid(model, voltage_path, thresholds, parameters, output_dir, population="excitatory"):
    for name, value in parameters.items():
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    defaults = {"jr": [4, 5, 6, 7, 8], "mdf": [1, 2, 3, 4, 5],
                "lw": [-40, -45, -50, -55, -60], "rrw": [-.010, -.005, 0, .005, .010]}
    threshold = _numbers(defaults[model] if thresholds is None else thresholds, "thresholds")
    grid = {"jr": (-5, 20, .001), "mdf": (-5, 20, .001),
            "lw": (-100, -20, .01), "rrw": (-.05, .05, .00001)}[model]
    voltage = _vector(voltage_path, "voltage", np.arange(*grid))
    functions = _helpers(parameters)
    rows = []
    for value in threshold:
        if model == "jr":
            row = [functions["sigm_Jansen"](parameters["nu_max"], value, parameters["r"], v) for v in voltage]
        elif model == "mdf":
            row = [functions["sigm_Moran"](v, value) for v in voltage]
        elif model == "lw":
            p = SimpleNamespace(S_e_max=parameters["S_max"], S_i_max=parameters["S_max"], mu_e=value,
                                mu_i=value, sigma_e=parameters["sigma"], sigma_i=parameters["sigma"])
            row = [functions["S_e" if population == "excitatory" else "S_i"](p, v) for v in voltage]
        else:
            row = [functions["sig"](v, parameters["Qmax"], value, parameters["sigma"]) for v in voltage]
        rows.append(row)
    settings = {"parameters": parameters, "thresholds": threshold.tolist(), "population": population,
                "voltage_units": "V" if model == "rrw" else "Input (units unspecified)" if model == "mdf" else "mV",
                "response_units": "Response (units unspecified)" if model == "mdf" else "s^-1"}
    if model == "mdf":
        settings["unit_notes"] = ("Source rho_1/rho_2 comments say na, but the shared plot labels input mV and response s^-1. "
                                  "MDF units are unspecified by the source; no conversion is applied.")
    return _save(model, "sigmoid", voltage, {"firing_rate": np.asarray(rows)}, settings, output_dir)


def _impulse(model, time_path, rates_e, rates_i, parameters, output_dir):
    for name, value in parameters.items():
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    default_e = [100, 200, 300, 400, 500] if model == "lw" else [50, 60, 83.33, 90, 100] if model == "rrw" else [50, 75, 100, 125, 150]
    default_i = [45, 55, 65, 75, 85] if model == "lw" else [25, 50, 75, 100, 125]
    excitatory = _numbers(default_e if rates_e is None else rates_e, "rates_e", positive=True)
    inhibitory = _numbers(default_i if rates_i is None else rates_i, "rates_i", positive=True)
    if model != "rrw" and len(excitatory) != len(inhibitory):
        raise ValueError("Excitatory and inhibitory rate vectors must have equal length, as paired in the source")
    time = _vector(time_path, "time_seconds", np.arange(0, .2, .001))
    if np.any(time < 0):
        raise ValueError("Impulse-response times must be nonnegative")
    functions = _helpers(parameters)
    if model == "rrw":
        if np.any(excitatory == parameters["beta"]):
            raise ValueError("alpha must differ from beta in the upstream RRW formula")
        curves = {"dendritic": np.asarray([[functions["imp_Robinson"](t, rate) for t in time] for rate in excitatory])}
        rates = {"dendritic": excitatory.tolist()}
    else:
        function = functions[{"jr": "imp_Jansen", "mdf": "imp_Moran", "lw": "imp_Liley"}[model]]
        paired = np.asarray([[function(t, e, i) for t in time] for e, i in zip(excitatory, inhibitory)])
        curves = {"excitatory": paired[:, :, 0], "inhibitory": paired[:, :, 1]}
        rates = {"excitatory": excitatory.tolist(), "inhibitory": inhibitory.tolist()}
    return _save(model, "impulse", time, curves, {"parameters": parameters, "rates": rates}, output_dir)


@sigmoid_and_impulse_response_mcp.tool()
def sigmoid_response_curve_jansen_rit(
    voltage_path: Annotated[str | None, Field(description="JSON/NPZ voltage vector in mV; None uses upstream grid")] = None,
    thresholds: Annotated[list[float] | None, Field(description="Firing thresholds v0 in mV; None uses upstream five-value sweep")] = None,
    nu_max: Annotated[float, "Maximum half firing rate in s^-1"] = 2.5,
    r: Annotated[float, "Sigmoid slope in mV^-1"] = .56,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Evaluate the upstream Jansen–Rit firing-rate sigmoid.
    Input is a voltage file and thresholds; output is curve arrays and a figure.
    """
    return _sigmoid("jr", voltage_path, thresholds, {"nu_max": nu_max, "r": r}, output_dir)


@sigmoid_and_impulse_response_mcp.tool()
def sigmoid_response_curve_moran_david_friston(
    voltage_path: Annotated[str | None, Field(description="JSON/NPZ MDF input grid; source comments say na but plot labels mV, so units are unspecified")] = None,
    thresholds: Annotated[list[float] | None, Field(description="MDF rho2 threshold values; None uses upstream sweep")] = None,
    rho_1: Annotated[float, "MDF sigmoid slope"] = 2.0,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Evaluate the upstream offset-corrected MDF sigmoid.
    Input is a voltage file and thresholds; output is curve arrays and a figure.
    """
    return _sigmoid("mdf", voltage_path, thresholds, {"rho_1": rho_1}, output_dir)


@sigmoid_and_impulse_response_mcp.tool()
def sigmoid_response_curve_liley_wright(
    voltage_path: Annotated[str | None, Field(description="JSON/NPZ voltage vector in mV; None uses upstream grid")] = None,
    thresholds: Annotated[list[float] | None, Field(description="LW mu threshold values in mV; None uses upstream sweep")] = None,
    S_max: Annotated[float, "Selected population maximum firing rate in s^-1"] = 500.0,
    sigma: Annotated[float, "Selected population threshold spread in mV"] = 5.0,
    population: Annotated[Literal["excitatory", "inhibitory"], "Select upstream S_e or S_i helper"] = "excitatory",
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Evaluate the upstream excitatory or inhibitory Liley–Wright sigmoid.
    Input is a voltage file and population parameters; output is curve arrays and a figure.
    """
    return _sigmoid("lw", voltage_path, thresholds, {"S_max": S_max, "sigma": sigma}, output_dir, population)


@sigmoid_and_impulse_response_mcp.tool()
def sigmoid_response_curve_robinson_rennie_wright(
    voltage_path: Annotated[str | None, Field(description="JSON/NPZ voltage vector in volts; None uses upstream grid")] = None,
    thresholds: Annotated[list[float] | None, Field(description="RRW theta thresholds in volts; None uses upstream sweep")] = None,
    Qmax: Annotated[float, "Maximum firing rate in s^-1"] = 340.0,
    sigma: Annotated[float, "Threshold spread in volts"] = .0038,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Evaluate the upstream Robinson–Rennie–Wright voltage-to-rate sigmoid.
    Input is a voltage file and thresholds; output is curve arrays and a figure.
    """
    return _sigmoid("rrw", voltage_path, thresholds, {"Qmax": Qmax, "sigma": sigma}, output_dir)


@sigmoid_and_impulse_response_mcp.tool()
def impulse_response_curve_jansen_rit(
    time_path: Annotated[str | None, Field(description="JSON/NPZ time_seconds vector; None uses upstream 0–199ms grid")] = None,
    rates_e: Annotated[list[float] | None, Field(description="Excitatory a values in s^-1; paired with rates_i")] = None,
    rates_i: Annotated[list[float] | None, Field(description="Inhibitory b values in s^-1; paired with rates_e")] = None,
    A: Annotated[float, "Excitatory amplitude in mV"] = 3.25,
    B: Annotated[float, "Inhibitory amplitude in mV"] = 22.0,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Evaluate the upstream Jansen–Rit synaptic impulse responses.
    Input is a time file and paired rate sweeps; output is excitatory/inhibitory arrays and a figure.
    """
    return _impulse("jr", time_path, rates_e, rates_i, {"A": A, "B": B}, output_dir)


@sigmoid_and_impulse_response_mcp.tool()
def impulse_response_curve_moran_david_friston(
    time_path: Annotated[str | None, Field(description="JSON/NPZ time_seconds vector; None uses upstream grid")] = None,
    rates_e: Annotated[list[float] | None, Field(description="Excitatory kappa_e values in s^-1; paired with rates_i")] = None,
    rates_i: Annotated[list[float] | None, Field(description="Inhibitory kappa_i values in s^-1; paired with rates_e")] = None,
    He: Annotated[float, "Excitatory amplitude in mV"] = 4.0,
    Hi: Annotated[float, "Inhibitory amplitude in mV"] = 32.0,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Evaluate the upstream MDF synaptic impulse responses.
    Input is a time file and paired rate sweeps; output is excitatory/inhibitory arrays and a figure.
    """
    return _impulse("mdf", time_path, rates_e, rates_i, {"He": He, "Hi": Hi}, output_dir)


@sigmoid_and_impulse_response_mcp.tool()
def impulse_response_curve_liley_wright(
    time_path: Annotated[str | None, Field(description="JSON/NPZ time_seconds vector; None uses upstream grid")] = None,
    rates_e: Annotated[list[float] | None, Field(description="Excitatory gamma_e values in s^-1; paired with rates_i")] = None,
    rates_i: Annotated[list[float] | None, Field(description="Inhibitory gamma_i values in s^-1; paired with rates_e")] = None,
    Gamma_e: Annotated[float, "Excitatory amplitude in mV"] = .71,
    Gamma_i: Annotated[float, "Inhibitory amplitude in mV"] = .71,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Evaluate the upstream Liley–Wright synaptic impulse responses.
    Input is a time file and paired rate sweeps; output is excitatory/inhibitory arrays and a figure.
    """
    return _impulse("lw", time_path, rates_e, rates_i, {"Gamma_e": Gamma_e, "Gamma_i": Gamma_i}, output_dir)


@sigmoid_and_impulse_response_mcp.tool()
def impulse_response_curve_robinson_rennie_wright(
    time_path: Annotated[str | None, Field(description="JSON/NPZ time_seconds vector; None uses upstream grid")] = None,
    alpha_values: Annotated[list[float] | None, Field(description="Slow dendritic rates in s^-1, each different from beta")] = None,
    beta: Annotated[float, "Fast dendritic rate in s^-1"] = 769.23,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Evaluate the upstream Robinson–Rennie–Wright dendritic impulse response.
    Input is a time file and rate sweep; output is response arrays and a figure.
    """
    return _impulse("rrw", time_path, alpha_values, None, {"beta": beta}, output_dir)
