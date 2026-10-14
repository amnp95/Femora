import pytest

from femora import Model


def recovery_tcl(factor_once):
    model = Model()
    analysis = model.analysis.transient(
        name="recovery",
        constraint_handler=model.analysis.constraint.plain(),
        numberer=model.analysis.numberer.parallelrcm(),
        system=model.analysis.system.mumps(),
        test=model.analysis.test.energyincr(tol=1e-4, max_iter=8),
        algorithm=model.analysis.algorithm.modifiednewton(factor_once=factor_once),
        integrator=model.analysis.integrator.newmark(gamma=0.5, beta=0.25),
        dt=0.01,
        final_time=1.0,
        max_retries=1,
        num_sublevels=3,
        num_substeps=2,
    )
    return "\n".join(analysis._transient_recovery_procedure("recovery"))


def test_plain_modified_newton_recovery_unchanged():
    assert "FemoraFactorOnceDt" not in recovery_tcl(False)


def test_factor_once_refreshes_on_subdivision_and_return():
    tkinter = pytest.importorskip("tkinter")
    interp = tkinter.Tcl()
    interp.eval("""
        set pid 1
        set attempts {}
        set refreshes 0
        set failures 2
        proc algorithm {args} {incr ::refreshes}
        proc analyze {count dt} {
            lappend ::attempts $dt
            if {$::failures > 0} {
                incr ::failures -1
                return -3
            }
            return 0
        }
    """)
    interp.eval(recovery_tcl(True))
    assert interp.eval("FemoraAnalyzeTransientStep 0.01 0") == "0"
    # Initial dt and subdivided dt refresh; retries and sibling steps reuse.
    assert interp.eval("set refreshes") == "2"
    assert interp.eval("set attempts") == "0.01 0.01 0.005 0.005"
    assert interp.eval("FemoraAnalyzeTransientStep 0.01 0") == "0"
    assert interp.eval("set refreshes") == "3"
    assert interp.eval("FemoraAnalyzeTransientStep 0.01 0") == "0"
    assert interp.eval("set refreshes") == "3"


def test_recovery_reinitializes_factor_once_tracking():
    assert recovery_tcl(True).startswith("set FemoraFactorOnceDt {}\n")
