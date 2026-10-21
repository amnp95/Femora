"""Smoke-test the top-to-bottom tutorial without importing it as a library."""
import ast
import os
from pathlib import Path
import subprocess

import pytest


EXAMPLES = Path(__file__).resolve().parents[2] / "examples/buildings"


@pytest.mark.parametrize("analysis_type", ["pushover", "earthquake"])
@pytest.mark.parametrize("nonlinear", [False, True])
def test_simple_frame_exports_and_postprocesses(tmp_path, monkeypatch, analysis_type, nonlinear):
    monkeypatch.chdir(tmp_path)
    path = EXAMPLES / "steel_concentrically_braced_frame_3d.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assert not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))
    settings = dict(analysis_type=analysis_type, nonlinear=nonlinear,
                    push_steps=3, roof_drift=0.0005, final_time=0.03)
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in settings:
                node.value = ast.Constant(settings[name])
    exec(compile(ast.fix_missing_locations(tree), str(path), "exec"), {"__file__": str(path)})
    case = tmp_path / f"example_outputs/frame_{analysis_type}_{'nonlinear' if nonlinear else 'elastic'}"
    tcl = (case / "model.tcl").read_text(encoding="utf-8")
    assert "force3D localForce3D" in tcl
    assert "recorder Node" not in tcl
    executable = os.environ.get("FEMORA_OPENSEES")
    if not executable:
        return
    subprocess.run([executable, str(case / "model.tcl")], check=True, capture_output=True)
    assert list((case / "results").glob("response*.vtkhdf"))
    import matplotlib
    matplotlib.use("Agg")
    post = EXAMPLES / "steel_concentrically_braced_frame_3d_postprocess.py"
    source = post.read_text().replace(
        'case = Path("example_outputs/frame_earthquake_nonlinear")', f"case = Path({str(case)!r})"
    ).replace("show_plots = True", "show_plots = False")
    exec(compile(source, str(post), "exec"), {})
    assert (case / "processed/summary.csv").is_file()
    assert (case / ("pushover.png" if analysis_type == "pushover" else "earthquake.png")).is_file()
