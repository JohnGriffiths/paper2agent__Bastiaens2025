"""Spectrum aperiodic fits extracted from Bastiaens' existing NumPy/FOOOF calls."""
from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Annotated, Literal

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import RendererAgg
import numpy as np
from fooof import FOOOF
from fastmcp import FastMCP
from pydantic import Field

REFERENCE = "https://github.com/GriffithsLab/Bastiaens2025_AlphaModels/blob/74f924beb50f60513ccb7efe065dcc1014d0c953/code/Estimate_1_f_component.py"
estimate_1_f_component_mcp = FastMCP(name="estimate_1_f_component")


def _load_spectrum(path: str, frequency_key: str, power_key: str) -> tuple[np.ndarray, np.ndarray]:
    with np.load(Path(path).expanduser(), allow_pickle=False) as data:
        if frequency_key not in data or power_key not in data:
            raise ValueError(f"Spectrum NPZ must contain keys {frequency_key!r} and {power_key!r}")
        frequency = np.asarray(data[frequency_key], dtype=float)
        power = np.asarray(data[power_key], dtype=float)
    if frequency.ndim != 1 or power.ndim != 1 or frequency.size != power.size or frequency.size < 2:
        raise ValueError("Frequency and power must be aligned one-dimensional arrays with at least two samples")
    if not np.isfinite(frequency).all() or not np.isfinite(power).all():
        raise ValueError("Frequency and power must be finite")
    return frequency, power


def _destination(output_dir: str | None, prefix: str) -> Path:
    base = Path(output_dir).expanduser().resolve() if output_dir else Path.cwd() / "outputs"
    base.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=base))


@estimate_1_f_component_mcp.tool()
def estimate_1f_slope_linear_fit(
    spectrum_path: Annotated[str, "NPZ containing aligned frequency and power arrays, selected using frequency_key and power_key."],
    pre_peak_index_range: Annotated[tuple[int, int | None], "Python start/stop slice for the pre-peak fit; null stop selects the end."],
    post_peak_index_range: Annotated[tuple[int, int | None], "Python start/stop slice for the post-peak fit; null stop selects the end."],
    full_range: Annotated[tuple[int, int | None], "Python start/stop slice for the full aperiodic fit; null stop selects the end."],
    frequency_key: Annotated[str, "NPZ key containing frequency in Hz."] = "freqs",
    power_key: Annotated[str, "NPZ key containing spectral power."] = "psd",
    output_dir: Annotated[str | None, Field(description="Output base directory; each call creates a fresh subdirectory.")] = None,
) -> dict:
    """Fit source log–log linear slopes in three user-selected spectral index windows.
    Spectrum NPZ and three index ranges → fit coefficients, full fitted curves, and source plot.
    """
    frequency, power = _load_spectrum(spectrum_path, frequency_key, power_key)
    destination = _destination(output_dir, "aperiodic_linear_")
    ranges = {"pre": pre_peak_index_range, "post": post_peak_index_range, "full": full_range}
    coefficients = {}
    arrays = {}
    with RendererAgg.lock:
        figure, axis = plt.subplots()
        axis.plot(frequency, power)
        try:
            for name, bounds in ranges.items():
                start, stop = bounds
                x, y = frequency[slice(start, stop)], power[slice(start, stop)]
                if x.size < 2 or np.unique(x).size < 2:
                    raise ValueError(f"{name} index range must select at least two distinct frequencies")
                if np.any(x <= 0) or np.any(y <= 0):
                    raise ValueError(f"{name} fit requires positive frequency and power in the selected index range")
                # Source lines77–85: three np.polyfit/log/polyval calculations,
                # merged by window name without changing their computation.
                fit = np.polyfit(np.log(x), np.log(y), 1)
                log_curve = np.polyval(fit, np.log(x))
                coefficients[name] = {"slope": float(fit[0]), "intercept": float(fit[1])}
                arrays.update({name + "_frequency": x, name + "_log_power_fit": log_curve, name + "_coefficients": fit})
                axis.plot(x, np.exp(log_curve), color="orange" if name == "full" else "red")
            axis.set_xscale("log")
            axis.set_yscale("log")
            axis.set_xlabel("Frequency")
            axis.set_ylabel("Power")
            figure.savefig(destination / "linear_fit.png", dpi=150, bbox_inches="tight")
        finally:
            plt.close(figure)
    np.savez(destination / "linear_fit.npz", **arrays)
    return {"message": "Source log-log linear fits completed in all three supplied windows.", "reference": REFERENCE,
            "artifacts": [{"description": "Native fit coefficients and full log-space fitted curves", "path": str(destination / "linear_fit.npz")},
                          {"description": "Source spectrum and fitted-window curves", "path": str(destination / "linear_fit.png")}],
            "sample_count": len(frequency), "fits": coefficients}


@estimate_1_f_component_mcp.tool()
def estimate_1f_fooof(
    spectrum_path: Annotated[str, "NPZ containing aligned frequency and power arrays, selected using frequency_key and power_key."],
    fit_freq_range: Annotated[tuple[float, float], "Lower and upper fit frequencies in Hz."],
    peak_width_limits: Annotated[tuple[float, float], "Lower and upper FOOOF peak bandwidth limits in Hz."] = (2.0, 8.0),
    aperiodic_mode: Annotated[Literal["fixed", "knee"], "FOOOF aperiodic fit parameterization."] = "knee",
    frequency_key: Annotated[str, "NPZ key containing frequency in Hz."] = "freqs",
    power_key: Annotated[str, "NPZ key containing spectral power."] = "psd",
    output_dir: Annotated[str | None, Field(description="Output base directory; each call creates a fresh subdirectory.")] = None,
) -> dict:
    """Fit the source FOOOF aperiodic component and oscillatory peaks to a spectrum.
    Spectrum NPZ and fit settings → native fit arrays, parameters, metrics, and source report figure.
    """
    frequency, power = _load_spectrum(spectrum_path, frequency_key, power_key)
    if not 0 < fit_freq_range[0] < fit_freq_range[1]:
        raise ValueError("fit_freq_range must contain increasing positive bounds")
    if not 0 < peak_width_limits[0] <= peak_width_limits[1]:
        raise ValueError("peak_width_limits must contain increasing positive bounds")
    destination = _destination(output_dir, "aperiodic_fooof_")
    # Source lines108–109. report() consists of fit(), print_results(), plot();
    # call fit/plot directly so protocol stdout does not receive the report.
    model = FOOOF(peak_width_limits=peak_width_limits, aperiodic_mode=aperiodic_mode, verbose=False)
    model.fit(frequency, power, fit_freq_range)
    with RendererAgg.lock:
        figure, axis = plt.subplots()
        try:
            model.plot(plt_log=True, ax=axis)
            figure.savefig(destination / "fooof_fit.png", dpi=150, bbox_inches="tight")
        finally:
            plt.close(figure)
    np.savez(destination / "fooof_fit.npz", frequencies=model.freqs, power_spectrum_log10=model.power_spectrum,
             fitted_log10=model.fooofed_spectrum_, aperiodic_params=model.aperiodic_params_,
             peak_params=model.peak_params_, gaussian_params=model.gaussian_params_)
    return {"message": "Source FOOOF aperiodic and oscillatory fit completed.", "reference": REFERENCE,
            "artifacts": [{"description": "Native FOOOF component parameters and full fitted log10 spectrum", "path": str(destination / "fooof_fit.npz")},
                          {"description": "FOOOF report figure", "path": str(destination / "fooof_fit.png")}],
            "sample_count": len(model.freqs), "peak_count": len(model.peak_params_), "aperiodic_mode": aperiodic_mode,
            "aperiodic_parameters": model.aperiodic_params_.tolist(), "r_squared": float(model.r_squared_), "error": float(model.error_)}
