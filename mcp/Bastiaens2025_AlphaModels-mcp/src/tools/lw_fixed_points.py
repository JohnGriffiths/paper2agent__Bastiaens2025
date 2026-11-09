"""Liley–Wright fixed points through the pinned source contour/Jacobian calculation."""
from __future__ import annotations

import ast
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

REFERENCE = "https://github.com/GriffithsLab/Bastiaens2025_AlphaModels/blob/74f924beb50f60513ccb7efe065dcc1014d0c953/code/LW_fixed_points.py"
SOURCE = Path(__file__).resolve().parents[2] / "repo/Bastiaens2025_AlphaModels/code/LW_fixed_points.py"
lw_fixed_points_mcp = FastMCP(name="lw_fixed_points")


def _source_calculation(parameters: dict) -> dict:
    tree = ast.parse(SOURCE.read_text())
    # Include both the contour-intersection search and its analytic Jacobian;
    # omit only the subsequent demonstration-specific marker lookup and plots.
    tree.body = [node for node in tree.body if node.end_lineno <= 137]
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in parameters:
                value = parameters[name]
                expression = "np.array(" + repr(value) + ")" if isinstance(value, list) else repr(value)
                node.value = ast.parse(expression, mode="eval").body
    ast.fix_missing_locations(tree)
    namespace = {"__name__": "__upstream_lw_fixed_points__"}
    exec(compile(tree, str(SOURCE), "exec"), namespace)
    return namespace


@lw_fixed_points_mcp.tool()
def liley_wright_fixed_points_stability(
    N_ei_b: Annotated[list[float], "Excitatory-to-inhibitory connectivity, paired by index with N_ie_b."],
    N_ie_b: Annotated[list[float], "Inhibitory-to-excitatory connectivity, paired by index with N_ei_b."],
    h_e_r: Annotated[float, "Excitatory resting membrane potential in mV."] = -70.0,
    h_i_r: Annotated[float, "Inhibitory resting membrane potential in mV."] = -70.0,
    h_ee_eq: Annotated[float, "Excitatory reversal potential onto excitatory population in mV."] = 45.0,
    h_ie_eq: Annotated[float, "Inhibitory reversal potential onto excitatory population in mV."] = -90.0,
    h_ei_eq: Annotated[float, "Excitatory reversal potential onto inhibitory population in mV."] = 45.0,
    h_ii_eq: Annotated[float, "Inhibitory reversal potential onto inhibitory population in mV."] = -90.0,
    Gamma_e: Annotated[float, "Excitatory postsynaptic amplitude in mV."] = 0.71,
    Gamma_i: Annotated[float, "Inhibitory postsynaptic amplitude in mV."] = 0.71,
    gamma_e: Annotated[float, "Excitatory synaptic rate in ms^-1."] = 0.3,
    gamma_i: Annotated[float, "Inhibitory synaptic rate in ms^-1."] = 0.065,
    N_ee_b: Annotated[float, "Excitatory-to-excitatory connectivity."] = 3000.0,
    N_ii_b: Annotated[float, "Inhibitory-to-inhibitory connectivity."] = 500.0,
    S_max: Annotated[float, "Maximum firing rate in ms^-1."] = 0.5,
    mu: Annotated[float, "Sigmoid membrane-potential threshold in mV."] = -50.0,
    sigma: Annotated[float, "Sigmoid membrane-potential spread in mV."] = 5.0,
    p_ee: Annotated[float, "Extracortical excitatory input onto excitatory population in ms^-1."] = 3.460,
    p_ei: Annotated[float, "Extracortical excitatory input onto inhibitory population in ms^-1."] = 5.070,
    tau_e: Annotated[float, "Excitatory membrane time constant in ms."] = 94.0,
    tau_i: Annotated[float, "Inhibitory membrane time constant in ms."] = 42.0,
    output_dir: Annotated[str | None, Field(description="Output base directory; a fresh subdirectory is created for each call.")] = None,
) -> dict:
    """Find paired-connectivity Liley–Wright fixed points and classify their linear stability.
    Paired connectivity arrays and model parameters → native coordinates, labeled table, and stability figure.
    """
    if not N_ei_b or len(N_ei_b) != len(N_ie_b):
        raise ValueError("N_ei_b and N_ie_b must be nonempty paired arrays of equal length")
    parameters = dict(N_ei_b=N_ei_b, N_ie_b=N_ie_b, h_e_r=h_e_r, h_i_r=h_i_r, h_ee_eq=h_ee_eq,
                      h_ie_eq=h_ie_eq, h_ei_eq=h_ei_eq, h_ii_eq=h_ii_eq, Gamma_e=Gamma_e, Gamma_i=Gamma_i,
                      gamma_e=gamma_e, gamma_i=gamma_i, N_ee_b=N_ee_b, N_ii_b=N_ii_b, S_max=S_max,
                      mu=mu, sigma=sigma, p_ee=p_ee, p_ei=p_ei, tau_e=tau_e, tau_i=tau_i)
    if not all(np.isfinite(np.asarray(value)).all() for value in parameters.values()):
        raise ValueError("Model parameters and connectivity arrays must be finite")
    if min(gamma_e, gamma_i, sigma, tau_e, tau_i) <= 0:
        raise ValueError("Synaptic rates, sigmoid spread, and membrane time constants must be positive")
    if h_ee_eq == h_e_r or h_ie_eq == h_e_r or h_ei_eq == h_i_r or h_ii_eq == h_i_r:
        raise ValueError("Resting and corresponding reversal potentials must differ")
    base = Path(output_dir).expanduser().resolve() if output_dir else Path.cwd() / "outputs"
    base.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix="lw_fixed_points_", dir=base))
    with RendererAgg.lock:
        prior_figures = set(plt.get_fignums())
        try:
            contour_figure = plt.figure()
            namespace = _source_calculation(parameters)
            contour_figure.savefig(destination / "contours.png", dpi=150, bbox_inches="tight")
            ve = np.asarray(namespace["all_fixed_y0"])
            vi = np.asarray(namespace["all_fixed_y1"])
            stability = np.asarray(namespace["stability"], dtype=int)
            np.savez(destination / "fixed_points.npz", N_ei_b=N_ei_b, N_ie_b=N_ie_b, Ve=ve, Vi=vi, unstable=stability)
            np.savetxt(destination / "fixed_points.csv", np.column_stack([N_ei_b, N_ie_b, ve, vi, stability]),
                       delimiter=",", header="N_ei_b,N_ie_b,Ve_mV,Vi_mV,unstable", comments="")
            figure, axis = plt.subplots(figsize=(4, 3))
            axis.scatter(N_ei_b, ve, color=plt.cm.Set1(1), label="stable")
            axis.scatter(np.asarray(N_ei_b)[stability == 1], ve[stability == 1], color=plt.cm.Set1(0), label="unstable")
            axis.set_xlabel("$N_{ei}$")
            axis.set_ylabel("Fixed point ($V_{e}$: mV)")
            axis.legend()
            figure.savefig(destination / "stability.png", dpi=150, bbox_inches="tight")
        finally:
            for number in set(plt.get_fignums()) - prior_figures:
                plt.close(number)
    return {"message": "Liley–Wright source contour intersections and eigenvalue classification completed.",
            "reference": REFERENCE,
            "artifacts": [{"description": description, "path": str((destination / filename).resolve())}
                          for filename, description in [("fixed_points.npz", "Native paired connectivity, membrane coordinates, and instability flags"),
                                                        ("fixed_points.csv", "Labeled fixed-point table"), ("stability.png", "Source stability scatter with demonstration markers omitted"),
                                                        ("contours.png", "Native zero-contour intersections used to identify fixed points")]],
            "pair_count": len(N_ei_b), "fixed_point_count": len(stability),
            "stable_count": int(np.sum(stability == 0)), "unstable_count": int(np.sum(stability == 1))}
