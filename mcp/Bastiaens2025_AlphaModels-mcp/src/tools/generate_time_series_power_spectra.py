"""Simulations extracted without equation changes from the pinned Bastiaens native script."""
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

REFERENCE = "https://github.com/GriffithsLab/Bastiaens2025_AlphaModels/blob/74f924beb50f60513ccb7efe065dcc1014d0c953/code/Generate_time_series_power_spectra.py"
SOURCE = Path(__file__).resolve().parents[2] / "repo/Bastiaens2025_AlphaModels/code/Generate_time_series_power_spectra.py"
SOURCE_SHA256 = "bf5dedc8bf24d3e44fa32b23a4423ca03c83d56b500ae79f9a172ef854715370"
generate_time_series_power_spectra_mcp = FastMCP(name="generate_time_series_power_spectra")


class _BindInputs(ast.NodeTransformer):
    """Bind source constants and duration-dependent sampling, leaving model equations intact."""
    def __init__(self, values, duration, dt, seed, rrw):
        self.values = values
        self.duration, self.dt, self.seed = duration, dt, seed
        self.resampled_count = int(round(duration * 100))
        self.sampling_hz = self.resampled_count / duration
        self.burn_in_count = int(round(10 * self.sampling_hz)) if rrw else 0
        self.segment = min(1000, self.resampled_count - self.burn_in_count)

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in self.values:
                node.value = ast.copy_location(ast.parse(f"__inputs__[{name!r}]", mode="eval").body, node.value)
            elif name in {"stim_time", "sim_time"}:
                node.value = ast.copy_location(ast.Constant(self.duration), node.value)
            elif name == "stop":
                node.value = ast.copy_location(ast.parse(f"{self.duration!r} + t0/2", mode="eval").body, node.value)
        return self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "signal" and node.func.attr == "resample":
                node.args[1] = ast.Constant(self.resampled_count)
        if ast.unparse(node.func) == "np.random.uniform":
            node.args[:2] = [ast.Name(id="__noise_low__", ctx=ast.Load()), ast.Name(id="__noise_high__", ctx=ast.Load())]
        elif ast.unparse(node.func) == "np.random.seed":
            node.args = [ast.Constant(self.seed)]
        elif isinstance(node.func, ast.Name) and node.func.id == "welch":
            for keyword in node.keywords:
                if keyword.arg == "fs":
                    keyword.value = ast.Constant(self.sampling_hz)
                elif keyword.arg == "nperseg":
                    keyword.value = ast.Constant(self.segment)
                elif keyword.arg == "noverlap":
                    keyword.value = ast.Constant(min(125, self.segment - 1))
        return self.generic_visit(node)

    def visit_Slice(self, node):
        # The native 20000:40000 display is 2–4 seconds at its default dt.
        if isinstance(node.lower, ast.Constant) and node.lower.value == 20000 and isinstance(node.upper, ast.Constant) and node.upper.value == 40000:
            low = 2 if self.duration > 2 else 0
            node.lower = ast.Constant(int(round(low / self.dt)))
            node.upper = ast.Constant(int(round(min(4, self.duration - 2*self.dt) / self.dt)))
        elif isinstance(node.lower, ast.Constant) and node.lower.value == 1000 and node.upper is None:
            node.lower = ast.Constant(self.burn_in_count)
        return self.generic_visit(node)


def _simulate(model, settings):
    settings = dict(settings)
    duration = settings.pop("duration_seconds")
    dt = settings.pop("dt_seconds")
    seed = settings.pop("seed")
    output_dir = settings.pop("output_dir")
    # Optional JR connections keep the native C-derived defaults unless supplied.
    settings = {name: value for name, value in settings.items() if value is not None}
    if not np.isfinite(duration) or not np.isfinite(dt) or duration <= 0 or dt <= 0:
        raise ValueError("duration_seconds and dt_seconds must be finite and positive")
    if int(round(duration * 100)) < (1002 if model == "rrw" else 2) or duration / dt < 3:
        raise ValueError("Need at least two resampled points (RRW retains its source 10-second Welch burn-in) and three native steps")
    if seed < 0 or seed >= 2**32:
        raise ValueError("seed must be an integer in [0, 2**32)")
    if any(not np.isfinite(v) for v in settings.values()):
        raise ValueError("Scientific parameters must be finite")
    positive = {"jr": ["tau_e", "tau_i", "r"], "mdf": ["kappa_e", "kappa_i"],
                "lw": ["tau_e", "tau_i", "sigma_e", "sigma_i", "gamma_ee", "gamma_ei", "gamma_ie", "gamma_ii"],
                "rrw": ["alpha", "beta", "gamma", "sigma", "sigma_r"]}
    if any(settings[name] <= 0 for name in positive[model]):
        raise ValueError("Model time/rate/width constants must be positive")
    if model == "jr" and settings["noise_low"] > settings["noise_high"]:
        raise ValueError("noise_low must not exceed noise_high")
    if model == "rrw" and (settings["phin"] < 0 or settings["t0"] < 0):
        raise ValueError("phin and t0 must be nonnegative")
    if model == "lw" and any(settings[equilibrium] == settings[rest] for equilibrium, rest in
                             [("h_ee_eq", "h_e_r"), ("h_ie_eq", "h_e_r"), ("h_ei_eq", "h_i_r"), ("h_ii_eq", "h_i_r")]):
        raise ValueError("Reversal potentials must differ from the corresponding resting potentials")
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Native source differs from the pinned implementation")
    tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
    bounds = {"jr": (10, 74, "output", "freqs_Jansen", "ps_vPN_Jansen"),
              "mdf": (74, 141, "output_Moran", "freqs_Moran", "ps_vPN_Moran"),
              "lw": (141, 263, "EEG", "freqs_Liley", "ps_vPN_Liley"),
              "rrw": (263, 368, "output_Zhao", "freqs_Robinson", "ps_vPN_Robinson")}
    low, high, output_name, freq_name, power_name = bounds[model]
    nodes = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)) or low <= n.lineno < high]
    inputs = dict(settings, dt=dt)
    bound = _BindInputs(inputs, duration, dt, seed, model == "rrw").visit(ast.Module(body=nodes, type_ignores=[]))
    ast.fix_missing_locations(bound)
    namespace = {"__inputs__": inputs, "__noise_low__": settings.get("noise_low"), "__noise_high__": settings.get("noise_high"), "__name__": "__upstream_binding__", "__file__": str(SOURCE)}
    base = Path(output_dir).expanduser().resolve() if output_dir else Path.cwd() / "outputs"
    base.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix=f"time_series_{model}_", dir=base))
    with RendererAgg.lock:
        state = np.random.get_state()
        figures = set(plt.get_fignums())
        try:
            np.random.seed(seed)
            exec(compile(bound, str(SOURCE), "exec"), namespace)
            output = np.asarray(namespace[output_name])
            frequency = np.asarray(namespace[freq_name])
            power = np.asarray(namespace[power_name])
            if not all(np.isfinite(x).all() for x in [output, frequency, power]):
                raise ValueError("Source simulation produced nonfinite results; reconsider parameters and integration step")
            time = np.asarray(namespace["time_array"])[:len(output)]
            array_path = folder / "time_series_spectrum.npz"
            np.savez_compressed(array_path, time_seconds=time, output=output, frequency_hz=frequency, power=power)
            new_figures = set(plt.get_fignums()) - figures
            if len(new_figures) != 1:
                raise RuntimeError("Expected one source time-series/spectrum figure")
            figure_path = folder / "time_series_spectrum.png"
            plt.figure(next(iter(new_figures))).savefig(figure_path, dpi=100)
        finally:
            np.random.set_state(state)
            for number in set(plt.get_fignums()) - figures:
                plt.close(number)
    metadata = dict(model=model, duration_seconds=duration, dt_seconds=dt, seed=seed, parameters=settings,
                    native_sample_count=len(output), resampled_sample_count=int(round(duration*100)),
                    spectrum_sampling_hz=int(round(duration*100))/duration, source=REFERENCE, source_sha256=SOURCE_SHA256,
                    output_units="s^-1" if model == "rrw" else "mV", frequency_units="Hz",
                    welch_burn_in_seconds=10 if model == "rrw" else 0,
                    integration="source Euler" if model == "jr" else "source Euler-Maruyama",
                    rng_policy="Isolated NumPy MT19937 seed; caller state restored under global plot lock",
                    source_note="Native LW/RRW one-sample trim and RRW half-delay time-axis offset retained; independent model seeds do not consume earlier models' random draws")
    metadata_path = folder / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    return {"message": f"Simulated {model}: {len(output)} native samples and {len(frequency)} spectrum bins", "reference": REFERENCE,
            "artifacts": [{"description": "Native time series and source Welch spectrum (frequency_hz/power)", "path": str(array_path)},
                          {"description": "Source time-series and spectrum figure", "path": str(figure_path)},
                          {"description": "Parameters, units and provenance", "path": str(metadata_path)}],
            "model": model, "sample_count": len(output), "frequency_count": len(frequency), "shape": list(output.shape),
            "duration_seconds": duration, "dt_seconds": dt, "spectrum_sampling_hz": int(round(duration*100))/duration, "seed": seed}

@generate_time_series_power_spectra_mcp.tool()
def simulate_jansen_rit_time_series(
    duration_seconds: Annotated[float, Field(description="Simulation length in seconds; RRW must exceed10s for its source burn-in")] = 100.0,
    dt_seconds: Annotated[float, Field(description="Source integration step in seconds; LW converts internally to ms")] = 0.0001,
    seed: Annotated[int, Field(description="NumPy MT19937 seed; each model runs independently")] = 20261106,
    A: Annotated[float, Field(description='Excitatory synaptic amplitude in mV')] = 3.25,
    B: Annotated[float, Field(description='Inhibitory synaptic amplitude in mV')] = 22.0,
    C: Annotated[float, Field(description='Source connectivity scale; C1=C,C2=0.8C,C3=C4=0.25C')] = 135.0,
    C1: Annotated[float | None, Field(description='Pyramidal-to-excitatory connection; None uses C')] = None,
    C2: Annotated[float | None, Field(description='Excitatory-to-pyramidal connection; None uses 0.8*C')] = None,
    C3: Annotated[float | None, Field(description='Pyramidal-to-inhibitory connection; None uses 0.25*C')] = None,
    C4: Annotated[float | None, Field(description='Inhibitory-to-pyramidal connection; None uses 0.25*C')] = None,
    v0: Annotated[float, Field(description='Sigmoid threshold in mV')] = 6.0,
    tau_e: Annotated[float, Field(description='Excitatory time constant in ms')] = 10.0,
    tau_i: Annotated[float, Field(description='Inhibitory time constant in ms')] = 20.0,
    nu_max: Annotated[float, Field(description='Half maximum firing rate in s^-1')] = 2.5,
    r: Annotated[float, Field(description='Sigmoid slope in mV^-1')] = 0.56,
    noise_low: Annotated[float, Field(description='Uniform input lower bound in s^-1; use500 for eyes open')] = 120.0,
    noise_high: Annotated[float, Field(description='Uniform input upper bound in s^-1; use700 for eyes open')] = 320.0,
    output_dir: Annotated[str | None, Field(description="Base output directory; each call creates a fresh subdirectory")] = None,
) -> dict:
    """Simulate the upstream jansen rit model and its Welch power spectrum.
    Duration, step, seed and source parameters → native time series, spectrum NPZ and source figure.
    """
    return _simulate('jr', locals())


@generate_time_series_power_spectra_mcp.tool()
def simulate_moran_david_friston_time_series(
    duration_seconds: Annotated[float, Field(description="Simulation length in seconds; RRW must exceed10s for its source burn-in")] = 100.0,
    dt_seconds: Annotated[float, Field(description="Source integration step in seconds; LW converts internally to ms")] = 0.0001,
    seed: Annotated[int, Field(description="NumPy MT19937 seed; each model runs independently")] = 20261106,
    H_e: Annotated[float, Field(description='Excitatory synaptic amplitude in mV')] = 10.0,
    H_i: Annotated[float, Field(description='Inhibitory synaptic amplitude in mV')] = 22.0,
    kappa_e: Annotated[float, Field(description='Excitatory rate constant in s^-1')] = 250.0,
    kappa_i: Annotated[float, Field(description='Inhibitory rate constant in s^-1')] = 62.5,
    gamma_1: Annotated[float, Field(description='Source connectivity parameter')] = 128.0,
    gamma_2: Annotated[float, Field(description='Source connectivity parameter')] = 128.0,
    gamma_3: Annotated[float, Field(description='Source connectivity parameter')] = 64.0,
    gamma_4: Annotated[float, Field(description='Source connectivity parameter')] = 64.0,
    gamma_5: Annotated[float, Field(description='Source connectivity parameter')] = 1.0,
    rho_1: Annotated[float, Field(description='Sigmoid slope')] = 2.0,
    rho_2: Annotated[float, Field(description='Sigmoid threshold')] = 1.0,
    a: Annotated[float, Field(description='Source adaptation parameter; zero in canonical resting state')] = 0.0,
    output_dir: Annotated[str | None, Field(description="Base output directory; each call creates a fresh subdirectory")] = None,
) -> dict:
    """Simulate the upstream moran david friston model and its Welch power spectrum.
    Duration, step, seed and source parameters → native time series, spectrum NPZ and source figure.
    """
    return _simulate('mdf', locals())


@generate_time_series_power_spectra_mcp.tool()
def simulate_liley_wright_time_series(
    duration_seconds: Annotated[float, Field(description="Simulation length in seconds; RRW must exceed10s for its source burn-in")] = 100.0,
    dt_seconds: Annotated[float, Field(description="Source integration step in seconds; LW converts internally to ms")] = 0.0001,
    seed: Annotated[int, Field(description="NumPy MT19937 seed; each model runs independently")] = 20261106,
    S_e_max: Annotated[float, Field(description='Excitatory maximum rate in ms^-1')] = 0.5,
    S_i_max: Annotated[float, Field(description='Inhibitory maximum rate in ms^-1')] = 0.5,
    h_e_r: Annotated[float, Field(description='Excitatory resting membrane potential in mV; also source initial potential')] = -70.0,
    h_i_r: Annotated[float, Field(description='Inhibitory resting membrane potential in mV; also source initial potential')] = -70.0,
    mu_e: Annotated[float, Field(description='Excitatory threshold in mV')] = -50.0,
    mu_i: Annotated[float, Field(description='Inhibitory threshold in mV')] = -50.0,
    sigma_e: Annotated[float, Field(description='Excitatory threshold spread in mV')] = 5.0,
    sigma_i: Annotated[float, Field(description='Inhibitory threshold spread in mV')] = 5.0,
    tau_e: Annotated[float, Field(description='Excitatory time constant in ms')] = 94.0,
    tau_i: Annotated[float, Field(description='Inhibitory time constant in ms')] = 42.0,
    h_ee_eq: Annotated[float, Field(description='Synaptic reversal potential in mV; eyes source h_ee_eq=4')] = 45.0,
    h_ei_eq: Annotated[float, Field(description='Synaptic reversal potential in mV; eyes source h_ee_eq=4')] = 45.0,
    h_ie_eq: Annotated[float, Field(description='Synaptic reversal potential in mV; eyes source h_ee_eq=4')] = -90.0,
    h_ii_eq: Annotated[float, Field(description='Synaptic reversal potential in mV; eyes source h_ee_eq=4')] = -90.0,
    Gamma_ee: Annotated[float, Field(description='Synaptic amplitude in mV')] = 0.71,
    Gamma_ei: Annotated[float, Field(description='Synaptic amplitude in mV')] = 0.71,
    Gamma_ie: Annotated[float, Field(description='Synaptic amplitude in mV')] = 0.71,
    Gamma_ii: Annotated[float, Field(description='Synaptic amplitude in mV')] = 0.71,
    gamma_ee: Annotated[float, Field(description='Synaptic rate constant in ms^-1')] = 0.3,
    gamma_ei: Annotated[float, Field(description='Synaptic rate constant in ms^-1')] = 0.3,
    gamma_ie: Annotated[float, Field(description='Synaptic rate constant in ms^-1')] = 0.065,
    gamma_ii: Annotated[float, Field(description='Synaptic rate constant in ms^-1')] = 0.065,
    p_ee: Annotated[float, Field(description='External excitatory-to-excitatory input in ms^-1')] = 3.46,
    p_ee_sd: Annotated[float, Field(description='External excitatory noise scale')] = 1.0,
    p_ei: Annotated[float, Field(description='External excitatory-to-inhibitory input in ms^-1; eyes open uses6')] = 5.07,
    N_ei_b: Annotated[float, Field(description='Local connectivity count')] = 3000.0,
    N_ee_b: Annotated[float, Field(description='Local connectivity count')] = 3000.0,
    N_ie_b: Annotated[float, Field(description='Local connectivity count')] = 500.0,
    N_ii_b: Annotated[float, Field(description='Local connectivity count')] = 500.0,
    output_dir: Annotated[str | None, Field(description="Base output directory; each call creates a fresh subdirectory")] = None,
) -> dict:
    """Simulate the upstream liley wright model and its Welch power spectrum.
    Duration, step, seed and source parameters → native time series, spectrum NPZ and source figure.
    """
    return _simulate('lw', locals())


@generate_time_series_power_spectra_mcp.tool()
def simulate_robinson_rennie_wright_time_series(
    duration_seconds: Annotated[float, Field(description="Simulation length in seconds; RRW must exceed10s for its source burn-in")] = 100.0,
    dt_seconds: Annotated[float, Field(description="Source integration step in seconds; LW converts internally to ms")] = 0.0001,
    seed: Annotated[int, Field(description="NumPy MT19937 seed; each model runs independently")] = 0,
    gamma: Annotated[float, Field(description='Cortical propagation rate in s^-1')] = 116.0,
    t0: Annotated[float, Field(description='Corticothalamic round-trip delay in seconds')] = 0.08,
    Qmax: Annotated[float, Field(description='Maximum rate in s^-1; source also uses it for reticular calls')] = 340.0,
    theta: Annotated[float, Field(description='Threshold in V; source also uses it for reticular calls')] = 0.01292,
    sigma: Annotated[float, Field(description='Threshold spread in V')] = 0.0038,
    sigma_r: Annotated[float, Field(description='Reticular threshold spread in V')] = 0.0038,
    phin_0: Annotated[float, Field(description='Mean external field in s^-1')] = 1.0,
    nu_ee: Annotated[float, Field(description='Source synaptic coupling in V s')] = 0.00303,
    nu_ei: Annotated[float, Field(description='Source synaptic coupling in V s')] = -0.006,
    nu_es: Annotated[float, Field(description='Source synaptic coupling in V s')] = 0.00206,
    nu_re: Annotated[float, Field(description='Source synaptic coupling in V s')] = 0.00033,
    nu_rs: Annotated[float, Field(description='Source synaptic coupling in V s')] = 3e-05,
    nu_se: Annotated[float, Field(description='Source synaptic coupling in V s')] = 0.00218,
    nu_sr: Annotated[float, Field(description='Source synaptic coupling in V s')] = -0.00083,
    nu_sn: Annotated[float, Field(description='Source synaptic coupling in V s')] = 0.00098,
    alpha: Annotated[float, Field(description='Slow dendritic rate in s^-1')] = 83.33,
    beta: Annotated[float, Field(description='Fast dendritic rate in s^-1')] = 769.23,
    phin: Annotated[float, Field(description='Source external noise variance factor')] = 0.0005,
    output_dir: Annotated[str | None, Field(description="Base output directory; each call creates a fresh subdirectory")] = None,
) -> dict:
    """Simulate the upstream robinson rennie wright model and its Welch power spectrum.
    Duration, step, seed and source parameters → native time series, spectrum NPZ and source figure.
    """
    return _simulate('rrw', locals())

