"""Local MCP access to the pinned Bastiaens alpha-model research code."""
from fastmcp import FastMCP

from tools.connectivity_heatmaps import connectivity_heatmaps_mcp
from tools.estimate_1_f_component import estimate_1_f_component_mcp
from tools.generate_analytical_power_spectrum import generate_analytical_power_spectrum_mcp
from tools.generate_time_series_power_spectra import generate_time_series_power_spectra_mcp
from tools.jr_fixed_points import jr_fixed_points_mcp
from tools.lw_fixed_points import lw_fixed_points_mcp
from tools.rate_constant_heatmap import rate_constant_heatmap_mcp
from tools.sigmoid_and_impulse_response import sigmoid_and_impulse_response_mcp

mcp = FastMCP(name="Bastiaens2025_AlphaModels")
mcp.mount(connectivity_heatmaps_mcp)
mcp.mount(estimate_1_f_component_mcp)
mcp.mount(generate_analytical_power_spectrum_mcp)
mcp.mount(generate_time_series_power_spectra_mcp)
mcp.mount(jr_fixed_points_mcp)
mcp.mount(lw_fixed_points_mcp)
mcp.mount(rate_constant_heatmap_mcp)
mcp.mount(sigmoid_and_impulse_response_mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
