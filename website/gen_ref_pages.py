"""
Generate the code reference pages and navigation.
"""

from pathlib import Path
import mkdocs_gen_files

# --- CONFIG: Folders to completely hide ---
SKIP_FOLDERS = {"gui", "constants", "constant", "styles", "utils"}

# 1. Setup the Navigation builder
nav = mkdocs_gen_files.Nav()

# 2. Point to source code
# Resolve relative to THIS file, not CWD
script_dir = Path(__file__).parent
src_root = (script_dir.parent / "src").resolve()

files = sorted(src_root.rglob("*.py"))
print(f"DEBUG: Found {len(files)} python files in {src_root}")

for path in files:
    module_path = path.relative_to(src_root).with_suffix("")
    doc_path = path.relative_to(src_root).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    # If any part of the path (folder or file) is in SKIP_FOLDERS, ignore it.
    if set(parts).intersection(SKIP_FOLDERS):
        continue
    
    # Skip files that have "gui" in their name (case-insensitive)
    if "gui" in parts[-1].lower():
        continue

    # Skip __init__, __main__, or known problematic files
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    # 3. Add this file to the Navigation Tree
    nav[parts] = doc_path.as_posix()

    # 4. Create the actual Markdown file stub
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

# 5. Write the Navigation Map
# build_literate_nav() returns a generator, so we must iterate or use writelines
with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())

# 6. Create a landing page for the Reference section
# This ensures /docs/reference/ serves a valid page instead of a directory listing
# 6. Create a landing page for the Reference section
# This ensures /docs/reference/ serves a valid page instead of a directory listing
# NOTE: This has been moved to a static file: website/docs/reference/index.md
# with mkdocs_gen_files.open("reference/index.md", "w") as fd:
#     pass