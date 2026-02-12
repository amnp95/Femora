import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..', 'src'))
sys.path.append(src_dir)

# Mock Material if needed, but ASDEmbeddedNodeElement3D doesn't use it
from femora.components.element import ASDEmbeddedNodeElement3D
from femora.core.element_base import ElementRegistry

def test_asd_embedded_node_3d():
    print("Testing ASDEmbeddedNodeElement3D...")
    
    # 1. Create element with minimal params
    # ndof can be 3, 4, or 6
    ele1 = ASDEmbeddedNodeElement3D(ndof=3)
    tcl1 = ele1.to_tcl(tag=10, nodes=[1, 2, 3, 4, 5])
    print(f"Minimal TCL: {tcl1}")
    expected1 = "element ASDEmbeddedNodeElement 10 1 2 3 4 5"
    if tcl1 != expected1:
        print(f"Error: expected '{expected1}' (len {len(expected1)})")
        print(f"got      '{tcl1}' (len {len(tcl1)})")
        sys.exit(1)

    # 2. Create element with all params
    ele2 = ASDEmbeddedNodeElement3D(ndof=6, rot=True, p=True, K=2e20, KP=3e19)
    tcl2 = ele2.to_tcl(tag=20, nodes=[10, 11, 12, 13, 14])
    print(f"Full TCL: {tcl2}")
    
    if "-rot" not in tcl2:
        print("Error: -rot flag missing")
        sys.exit(1)
    if "-p" not in tcl2:
        print("Error: -p flag missing")
        sys.exit(1)
    if "-K 2e+20" not in tcl2 and "-K 2.0e+20" not in tcl2:
        print("Error: -K parameter missing or incorrect")
        sys.exit(1)
    if "-KP 3e+19" not in tcl2 and "-KP 3.0e+19" not in tcl2:
        print("Error: -KP parameter missing or incorrect")
        sys.exit(1)

    # 4. Test contact params
    ele3 = ASDEmbeddedNodeElement3D(ndof=3, contact=True, Kn=1e10, Kt=2e10, mu=0.3, orient=[0, 0, 1])
    tcl3 = ele3.to_tcl(tag=30, nodes=[1, 2, 3, 4, 5])
    print(f"Contact TCL (orient): {tcl3}")
    if "-contact 10000000000.0 20000000000.0 0.3" not in tcl3:
        print("Error: contact parameters missing or incorrect")
        sys.exit(1)
    if "-orient 0.0 0.0 1.0" not in tcl3:
        print("Error: orient parameter missing or incorrect")
        sys.exit(1)
    if "-int_type 1" not in tcl3:
        print("Error: default -int_type 1 missing")
        sys.exit(1)

    # 5. Test contact with orient_map
    ele4 = ASDEmbeddedNodeElement3D(ndof=3, contact=True, orient_map={1: [1, 1, 0]})
    tcl4 = ele4.to_tcl(tag=40, nodes=[1, 2, 3, 4, 5])
    print(f"Contact TCL (orient_map): {tcl4}")
    if "-orient 1.0 1.0 0.0" not in tcl4:
        print("Error: orient_map lookup failed or incorrect")
        sys.exit(1)
    if "-int_type 1" not in tcl4:
        print("Error: default -int_type 1 missing (with orient_map)")
        sys.exit(1)

    # 6. Test contact with -p and -rot
    ele5 = ASDEmbeddedNodeElement3D(ndof=6, rot=True, p=True, contact=True, Kn=5e9, Kt=5e9, mu=0.2)
    tcl5 = ele5.to_tcl(tag=50, nodes=[1, 2, 3, 4, 5])
    print(f"Contact TCL (rot + p): {tcl5}")
    if "-rot" not in tcl5 or "-p" not in tcl5:
        print("Error: -rot or -p flags missing in combined test")
        sys.exit(1)
    if "-contact 5000000000.0 5000000000.0 0.2" not in tcl5:
        print("Error: contact parameters missing in combined test")
        sys.exit(1)
    if "-int_type 1" not in tcl5:
        print("Error: default -int_type 1 missing (combined flags)")
        sys.exit(1)

    # 7. Test explicit integration type 0
    ele6 = ASDEmbeddedNodeElement3D(ndof=3, contact=True, int_type=0)
    tcl6 = ele6.to_tcl(tag=60, nodes=[1, 2, 3, 4, 5])
    print(f"Contact TCL (int_type=0): {tcl6}")
    if "-int_type 0" not in tcl6:
        print("Error: explicit -int_type 0 not honored")
        sys.exit(1)

    print("All tests passed!")

if __name__ == "__main__":
    test_asd_embedded_node_3d()
