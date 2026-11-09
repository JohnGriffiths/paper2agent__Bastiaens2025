"""Jansen–Rit fixed-point analysis from the pinned Bastiaens research script."""
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

REFERENCE = "https://github.com/GriffithsLab/Bastiaens2025_AlphaModels/blob/74f924beb50f60513ccb7efe065dcc1014d0c953/code/JR_fixed_points.py"
SOURCE = Path(__file__).resolve().parents[2] / "repo/Bastiaens2025_AlphaModels/code/JR_fixed_points.py"
jr_fixed_points_mcp = FastMCP(name="jr_fixed_points")


def _source_calculation(parameters: dict) -> dict:
    """Bind inputs into the original source statements; do not replace its calculation."""
    tree = ast.parse(SOURCE.read_text())
    # End before the demonstration-only marker search and plot. The initial
    # scatter is replaced by the final source stable/unstable scatter below.
    tree.body = [node for node in tree.body if node.end_lineno <= 96 and node.lineno not in (2, 3, 4, 5, 6, 37, 51, 53, 54, 55)]
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in parameters:
                value = parameters[name]
                expression = "np.array(" + repr(value) + ")" if isinstance(value, list) else repr(value)
                node.value = ast.parse(expression, mode="eval").body
    ast.fix_missing_locations(tree)
    namespace = {"__name__": "__upstream_jr_fixed_points__"}
    exec(compile(tree, str(SOURCE), "exec"), namespace)
    return namespace


@jr_fixed_points_mcp.tool()
def jansen_rit_fixed_points_stability(
    C3_proportions: Annotated[list[float], Field(description="Paired C3/C connectivity proportions, one per sweep point.")],
    C4_proportions: Annotated[list[float], Field(description="Paired C4/C connectivity proportions, aligned with C3_proportions.")],
    p: Annotated[float, Field(description="External input rate in s^-1.")] = 220.0,
    A: Annotated[float, Field(description="Excitatory synaptic amplitude in mV.")] = 3.25,
    B: Annotated[float, Field(description="Inhibitory synaptic amplitude in mV.")] = 22.0,
    C: Annotated[float, Field(description="Base connectivity constant C1; source C2 equals0.8*C.")] = 135.0,
    v0: Annotated[float, Field(description="Sigmoid firing threshold in mV.")] = 6.0,
    a: Annotated[float, Field(description="Excitatory synaptic rate in s^-1.")] = 100.0,
    b: Annotated[float, Field(description="Inhibitory synaptic rate in s^-1.")] = 50.0,
    vmax: Annotated[float, Field(description="Half the maximum sigmoid firing rate in s^-1.")] = 2.5,
    r: Annotated[float, Field(description="Sigmoid steepness in mV^-1.")] = 0.56,
    output_dir: Annotated[str | None, Field(description="Output base directory; each call creates a fresh subdirectory.")] = None,
) -> dict:
    """Find paired-connectivity Jansen–Rit fixed points and classify their linear stability.
    Connectivity proportions and model parameters → native arrays, labeled table, and stability figure.
    """
    if not C3_proportions or len(C3_proportions) != len(C4_proportions):
        raise ValueError("C3_proportions and C4_proportions must be nonempty paired arrays of equal length")
    parameters = dict(C3_all=C3_proportions, C4_all=C4_proportions, p=p, A=A, B=B, C=C, v0=v0, a=a, b=b, vmax=vmax, r=r)
    if not all(np.isfinite(np.asarray(value)).all() for value in parameters.values()):
        raise ValueError("Model parameters and connectivity proportions must be finite")
    if a <= 0 or b <= 0:
        raise ValueError("Synaptic rates a and b must be positive")
    base = Path(output_dir).expanduser().resolve() if output_dir else Path.cwd() / "outputs"
    base.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix="jr_fixed_points_", dir=base))
    with RendererAgg.lock:
        namespace = _source_calculation(parameters)
        values = namespace["new_values"]
        counts = np.asarray([len(value) for value in values], dtype=int)
        fixed_points = np.concatenate(values) if counts.sum() else np.empty(0)
        stability = np.asarray(namespace["stability_connection"], dtype=int)
        c3 = np.repeat(np.asarray(C3_proportions) * C, counts)
        c4 = np.repeat(np.asarray(C4_proportions) * C, counts)
        np.savez(destination / "fixed_points.npz", C3_proportions=C3_proportions, C4_proportions=C4_proportions,
                 counts=counts, C3=c3, C4=c4, fixed_points=fixed_points, unstable=stability)
        np.savetxt(destination / "fixed_points.csv", np.column_stack([c3, c4, fixed_points, stability]),
                   delimiter=",", header="C3,C4,fixed_point_mV,unstable", comments="")
        # Source lines112–123: stable points followed by unstable overlay;
        # demonstration marker lookup is intentionally absent for arbitrary grids.
        figure, axis = plt.subplots(figsize=(4, 3))
        axis.scatter(c3, fixed_points, color=plt.cm.Set1(1), label="stable")
        axis.scatter(c3[stability == 1], fixed_points[stability == 1], color=plt.cm.Set1(0), label="unstable")
        axis.set_xlabel("Connectivity C3")
        axis.set_ylabel("Fixed point (y1-y2: mV)")
        axis.legend()
        figure.savefig(destination / "stability.png", dpi=150, bbox_inches="tight")
        plt.close(figure)
    return {"message": "Jansen–Rit source fixed-point and eigenvalue classification completed.", "reference": REFERENCE,
            "artifacts": [{"description": description, "path": str((destination / filename).resolve())}
                          for filename, description in [("fixed_points.npz", "Native fixed points, paired connectivity, counts, and instability flags"),
                                                        ("fixed_points.csv", "Labeled fixed-point table"), ("stability.png", "Source stability scatter with demonstration markers omitted")]],
            "pair_count": len(C3_proportions), "fixed_point_count": len(stability),
            "stable_count": int(np.sum(stability == 0)), "unstable_count": int(np.sum(stability == 1))}
