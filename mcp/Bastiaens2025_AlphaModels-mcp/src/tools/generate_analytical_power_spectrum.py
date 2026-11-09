"""Analytical spectra bound to the pinned Bastiaens upstream source sections."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Annotated

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import RendererAgg
import numpy as np
from fastmcp import FastMCP
from pydantic import Field

REFERENCE = "https://github.com/GriffithsLab/Bastiaens2025_AlphaModels/blob/74f924beb50f60513ccb7efe065dcc1014d0c953/code/Generate_analytical_power_spectrum.py"
SOURCE = Path(__file__).resolve().parents[2] / "repo/Bastiaens2025_AlphaModels/code/Generate_analytical_power_spectrum.py"
SOURCE_SHA256 = "37f41e0b564a626bfcb5352208621e698ba305681d602fe40d20b312557cc5d1"
generate_analytical_power_spectrum_mcp = FastMCP(name="generate_analytical_power_spectrum")


class _BindInputs(ast.NodeTransformer):
    def __init__(self, names):
        self.names = names

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in self.names:
                node.value = ast.copy_location(ast.parse(f"__inputs__[{name!r}]", mode="eval").body, node.value)
        return self.generic_visit(node)


def _frequencies(path):
    if path is None:
        return None
    path = Path(path).expanduser().resolve(strict=True)
    if path.suffix.lower() == ".npz":
        with np.load(path, allow_pickle=False) as data:
            if "frequency_hz" not in data:
                raise ValueError("Frequency NPZ requires a frequency_hz array")
            values = np.asarray(data["frequency_hz"], dtype=float)
    elif path.suffix.lower() == ".json":
        data = json.loads(path.read_text())
        values = np.asarray(data["frequency_hz"] if isinstance(data, dict) else data, dtype=float)
    else:
        raise ValueError("frequency_path must be a JSON array/object or NPZ with frequency_hz")
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all() or np.any(values <= 0) or np.any(np.diff(values) <= 0):
        raise ValueError("Frequencies must be a finite, positive, strictly increasing vector with at least two entries")
    return values


def _evaluate(model, parameters, frequency_path, output_dir):
    for name, value in parameters.items():
        if not np.isfinite(value):
            raise ValueError(f"{name} must be finite")
    positive = {
        "jr": ["nu_max", "r", "Hee", "Hii", "tau_e", "tau_i"],
        "mdf": ["kappa_e", "kappa_i", "H_e", "H_i", "rho_1"],
        "lw": ["Gamma_e", "Gamma_i", "gamma_e", "gamma_i", "tau_e", "tau_i", "S_e_max", "S_i_max", "sigma_e", "sigma_i"],
        "rrw": ["alpha", "beta", "gamma_e", "r_e"],
    }
    if any(parameters[k] <= 0 for k in positive[model]):
        raise ValueError("Rate, gain, width and time constants must be positive")
    if model == "rrw" and parameters["mean_square_noise"] < 0:
        raise ValueError("mean_square_noise must be nonnegative")
    frequency = _frequencies(frequency_path)
    text = SOURCE.read_text()
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Upstream analytical source differs from the pinned implementation")
    source_tree = ast.parse(text, filename=str(SOURCE))
    bounds = {"jr": (10, 41, "y_f"), "mdf": (41, 106, "Habs_new"),
              "lw": (134, 230, "Power"), "rrw": (230, 276, "Power1")}
    low, high, result_name = bounds[model]
    nodes = [n for n in source_tree.body if n.lineno < 10 or low <= n.lineno < high]
    inputs = dict(parameters)
    if frequency is not None:
        inputs["freq"] = frequency
    tree = _BindInputs(inputs).visit(ast.Module(body=nodes, type_ignores=[]))
    ast.fix_missing_locations(tree)
    namespace = {"__inputs__": inputs, "__name__": "__upstream_binding__", "__file__": str(SOURCE)}
    base = Path(output_dir).expanduser().resolve() if output_dir else Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix=f"bastiaens_analytical_{model}_", dir=base))
    with RendererAgg.lock:
        previous = set(plt.get_fignums())
        try:
            exec(compile(tree, str(SOURCE), "exec"), namespace)
            hz = np.asarray(namespace["freq"], dtype=float)
            power = np.asarray(namespace[result_name], dtype=float).reshape(-1)
            if power.shape != hz.shape or not np.isfinite(power).all():
                raise ValueError("Upstream computation produced an invalid or nonfinite spectrum")
            array_path = folder / "spectrum.npz"
            figure_path = folder / "spectrum.png"
            np.savez(array_path, frequency_hz=hz, power=power)
            new_figures = set(plt.get_fignums()) - previous
            if len(new_figures) != 1:
                raise RuntimeError("Expected one figure from the selected upstream model block")
            plt.figure(next(iter(new_figures))).savefig(figure_path, dpi=160)
        finally:
            for number in set(plt.get_fignums()) - previous:
                plt.close(number)
    metadata = folder / "metadata.json"
    metadata.write_text(json.dumps({"model": model, "parameters": parameters, "source": REFERENCE,
                                    "source_sha256": SOURCE_SHA256, "frequency_count": len(hz),
                                    "frequency_units": "Hz", "power_units": "upstream arbitrary units"}, indent=2) + "\n")
    return {"message": f"Computed {model} analytical power spectrum at {len(hz)} frequencies", "reference": REFERENCE,
            "artifacts": [{"description": "Frequency and power arrays", "path": str(array_path)},
                          {"description": "Upstream spectrum figure", "path": str(figure_path)},
                          {"description": "Parameters and source provenance", "path": str(metadata)}],
            "model": model, "num_frequencies": len(hz), "shape": list(power.shape)}


@generate_analytical_power_spectrum_mcp.tool()
def analytical_power_spectrum_jansen_rit(
    frequency_path: Annotated[str | None, Field(description="JSON/NPZ frequency_hz vector; None uses upstream 1–60 Hz, 200 points")] = None,
    nu_max: Annotated[float, "Maximum half firing rate in s^-1"] = 2.5,
    r: Annotated[float, "Sigmoid slope in mV^-1"] = 0.56,
    Hee: Annotated[float, "Excitatory synaptic amplitude in mV"] = 3.25,
    tau_e: Annotated[float, "Excitatory time constant in seconds"] = 0.040,
    Hii: Annotated[float, "Inhibitory synaptic amplitude in mV"] = 22.0,
    tau_i: Annotated[float, "Inhibitory time constant in seconds"] = 0.052,
    C1: Annotated[float, "Excitatory connectivity C1"] = 135.0,
    C2: Annotated[float, "Excitatory connectivity C2"] = 108.0,
    C3: Annotated[float, "Excitatory to inhibitory connectivity C3"] = 33.75,
    C4: Annotated[float, "Inhibitory to excitatory connectivity C4"] = 33.75,
    v0: Annotated[float, "Upstream threshold parameter in mV; not used in this linearized formula"] = 6.0,
    P: Annotated[float, "Mean external input in s^-1"] = 220.0,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Compute the upstream Jansen–Rit linearized analytical spectrum.
    Input is a frequency file and model parameters; output is spectrum arrays and a figure.
    """
    values = locals().copy()
    return _evaluate("jr", {k: v for k, v in values.items() if k not in ["frequency_path", "output_dir"]}, frequency_path, output_dir)


@generate_analytical_power_spectrum_mcp.tool()
def analytical_power_spectrum_moran_david_friston(
    frequency_path: Annotated[str | None, Field(description="JSON/NPZ frequency_hz vector; None uses upstream grid")] = None,
    kappa_e: Annotated[float, "Excitatory rate constant in s^-1"] = 250.0,
    kappa_i: Annotated[float, "Inhibitory rate constant in s^-1"] = 62.5,
    H_e: Annotated[float, "Excitatory synaptic amplitude in mV"] = 10.0,
    H_i: Annotated[float, "Inhibitory synaptic amplitude in mV"] = 22.0,
    gamma_1: Annotated[float, "Connectivity gamma1"] = 128.0,
    gamma_2: Annotated[float, "Connectivity gamma2"] = 128.0,
    gamma_3: Annotated[float, "Connectivity gamma3"] = 64.0,
    gamma_4: Annotated[float, "Connectivity gamma4"] = 64.0,
    gamma_5: Annotated[float, "Connectivity gamma5"] = 1.0,
    rho_1: Annotated[float, "Sigmoid slope"] = 2.0,
    rho_2: Annotated[float, "Sigmoid threshold"] = 1.0,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Compute the upstream MDF state-space analytical spectrum.
    Input is a frequency file and model parameters; output is spectrum arrays and a figure.
    """
    values = locals().copy()
    return _evaluate("mdf", {k: v for k, v in values.items() if k not in ["frequency_path", "output_dir"]}, frequency_path, output_dir)


@generate_analytical_power_spectrum_mcp.tool()
def analytical_power_spectrum_liley_wright(
    frequency_path: Annotated[str | None, Field(description="JSON/NPZ frequency_hz vector; source converts Hz to kHz internally")] = None,
    h_e: Annotated[float, "Excitatory operating potential in mV"] = -66.5987,
    h_i: Annotated[float, "Inhibitory operating potential in mV"] = -58.5631,
    h_erest: Annotated[float, "Excitatory resting potential in mV"] = -69.6952,
    h_irest: Annotated[float, "Inhibitory resting potential in mV"] = -74.4255,
    N_ee_b: Annotated[float, "Local excitatory to excitatory connectivity"] = 2847.80,
    N_ei_b: Annotated[float, "Local excitatory to inhibitory connectivity"] = 4422.60,
    N_ie_b: Annotated[float, "Local inhibitory to excitatory connectivity"] = 744.01,
    N_ii_b: Annotated[float, "Local inhibitory to inhibitory connectivity"] = 173.86,
    Gamma_e: Annotated[float, "Excitatory synaptic amplitude in mV"] = 1.9827,
    Gamma_i: Annotated[float, "Inhibitory synaptic amplitude in mV"] = 0.4169,
    gamma_e: Annotated[float, "Excitatory rate in ms^-1"] = 0.3030,
    gamma_i: Annotated[float, "Inhibitory rate in ms^-1"] = 0.0486,
    tau_e: Annotated[float, "Excitatory membrane time constant in ms"] = 106.1237,
    tau_i: Annotated[float, "Inhibitory membrane time constant in ms"] = 69.5959,
    S_e_max: Annotated[float, "Excitatory maximum firing rate in ms^-1"] = 0.2943,
    S_i_max: Annotated[float, "Inhibitory maximum firing rate in ms^-1"] = 0.0671,
    mu_e: Annotated[float, "Excitatory threshold in mV"] = -40.0612,
    mu_i: Annotated[float, "Inhibitory threshold in mV"] = -52.8817,
    sigma_e: Annotated[float, "Excitatory threshold spread in mV"] = 3.8213,
    sigma_i: Annotated[float, "Inhibitory threshold spread in mV"] = 2.4760,
    h_eeq: Annotated[float, "Excitatory reversal potential in mV"] = -2.5335,
    h_ieq: Annotated[float, "Inhibitory reversal potential in mV"] = -87.5723,
    p_ee: Annotated[float, "External excitatory to excitatory input in ms^-1"] = 3.1560,
    p_ei: Annotated[float, "External excitatory to inhibitory input in ms^-1"] = 2.6976,
    p_ie: Annotated[float, "External inhibitory to excitatory input in ms^-1"] = 0.0,
    p_ii: Annotated[float, "External inhibitory to inhibitory input in ms^-1"] = 0.0,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Compute the upstream Liley–Wright fixed-point linearization spectrum.
    Input is a frequency file and operating-point parameters; output is spectrum arrays and a figure.
    """
    values = locals().copy()
    return _evaluate("lw", {k: v for k, v in values.items() if k not in ["frequency_path", "output_dir"]}, frequency_path, output_dir)


@generate_analytical_power_spectrum_mcp.tool()
def analytical_power_spectrum_robinson_rennie_wright(
    frequency_path: Annotated[str | None, Field(description="JSON/NPZ frequency_hz vector; None uses upstream grid")] = None,
    G_ei: Annotated[float, "Intracortical inhibitory loop gain"] = -4.11,
    G_ee: Annotated[float, "Intracortical excitatory loop gain"] = 2.07,
    G_es: Annotated[float, "Relay to cortical gain"] = 0.77,
    G_sn: Annotated[float, "External to relay gain"] = 8.10,
    G_se: Annotated[float, "Cortical to relay gain"] = 7.77,
    G_sr: Annotated[float, "Reticular to relay gain"] = -3.3,
    G_rs: Annotated[float, "Relay to reticular gain"] = 0.2,
    G_re: Annotated[float, "Cortical to reticular gain"] = 0.66,
    alpha: Annotated[float, "Slow dendritic rate constant in s^-1"] = 83.0,
    beta: Annotated[float, "Fast dendritic rate constant in s^-1"] = 769.0,
    gamma_e: Annotated[float, "Cortical propagation rate in s^-1"] = 116.0,
    t0: Annotated[float, "Corticothalamic delay in seconds"] = 0.085,
    r_e: Annotated[float, "Axonal range in metres"] = 0.086,
    mean_square_noise: Annotated[float, "Mean-square external noise amplitude"] = 1.0,
    output_dir: Annotated[str | None, Field(description="Base directory for a fresh output subdirectory")] = None,
) -> dict:
    """Compute the upstream Robinson–Rennie–Wright analytical spectrum.
    Input is a frequency file and loop gains; output is spectrum arrays and a figure.
    """
    values = locals().copy()
    return _evaluate("rrw", {k: v for k, v in values.items() if k not in ["frequency_path", "output_dir"]}, frequency_path, output_dir)
