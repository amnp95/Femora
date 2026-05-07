# Femora Docstring Standard

This file is the single source of truth for docstrings in `src/femora`.

The goal is a strict, repeatable Femora docstring format that:

- renders cleanly in MkDocs
- stays consistent across different AI tools
- matches real Femora usage patterns

---

## 1. Rendering Model

Femora API docs are rendered with `mkdocstrings` and
`merge_init_into_class: true`.

This means:

- the class page is class-first
- the main explanation should come from the class docstring
- constructor parameters should come from the `__init__` docstring
- examples written in the class docstring will appear on the class page

Because of this, class docstrings and `__init__` docstrings must have different
responsibilities.

---

## 2. Core Rules

These rules apply to all Femora Python files.

1. Every class should have a complete docstring.
2. Every method should have a complete docstring, whether it is public or
   private.
3. Do not change code logic, names, signatures, imports, or behavior when
   editing docstrings.
4. Keep wording factual, technical, and concise.
5. Explain the concept of a class or method when that explanation is necessary
   to understand what it represents or does.
6. Do not use REPL style `>>>`.
7. If an example is included, it must use fenced `python` code blocks.
8. If an example is included for normal Femora usage, prefer manager-based
   creation through:

   ```python
   import femora as fm

   model = fm.MeshMaker()
   ```

9. If type hints already exist in the signature, do not repeat types in
   parentheses in `Args`.
10. Use the section labels in this file exactly.
11. An AI may read related project files for context before writing docstrings,
    especially managers, base classes, and nearby components.

---

## 3. Class vs. Constructor Responsibilities

### Class docstring documents:

- what the class represents
- what it does
- when it should be used
- conceptual context when needed
- Tcl/OpenSees form if relevant
- required examples
- user-facing attributes if useful

### `__init__` docstring documents:

- how to create the object
- constructor arguments
- constructor validation and raised errors

### Do not put in the class docstring:

- a duplicate full `Args:` section that belongs in `__init__`
- repetitive constructor validation details

### Do not put in `__init__`:

- long conceptual explanation that belongs to the class
- `Returns:`
- example-heavy usage guidance unless there is a special reason

---

## 4. Required Class Docstring Format

Every class docstring should use this structure and order:

1. Summary line
2. Short description paragraph
3. `Tcl form:` if applicable
4. `Notes:` if needed
5. `Attributes:` if needed
6. `Examples:` required for classes

### Class template

```python
class SomeComponent:
    """One-line summary.

    Short paragraph describing what the component represents, what it does, and
    when it should be used.

    Tcl form:
        ``command Name <arg1> <arg2> ...``

    Notes:
        Add only meaningful user-facing or developer-facing notes here.

    Attributes:
        tag: Manager-assigned identifier after the object is added to a Femora
            manager.

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        component = model.some_manager.some_factory(...)
        print(component.tag)
        ```
    """
```

### Class rules

- The summary line must be a single sentence.
- The description should usually be one short paragraph.
- `Tcl form:` is required for classes that directly emit Tcl commands or Tcl
  blocks.
- `Notes:` is optional.
- `Attributes:` is optional.
- Every class must include at least one example.
- Prefer manager-based creation through `model = fm.MeshMaker()` when that is
  the normal API.

---

## 5. Required `__init__` Docstring Format

Every constructor docstring should use this structure and order:

1. Summary line
2. `Args:` if the constructor has parameters
3. `Raises:` if the constructor validates and raises
4. `Notes:` if truly needed

### Constructor template

```python
def __init__(self, a: int, b: float = 1.0):
    """Create a component with validated inputs.

    Args:
        a: Description of the first argument.
        b: Optional description of the second argument.

    Raises:
        ValueError: If the provided values are invalid.
    """
```

### Constructor rules

- Use `Args:` for constructor parameters.
- Use `Raises:` only when the constructor actually raises.
- Do not add `Returns:` to `__init__`.
- Keep conceptual explanation in the class docstring, not `__init__`.

---

## 6. Method Docstring Format

Every method docstring should be complete, whether the method is public or
private.

Use this order:

1. Summary line
2. Short explanation if the behavior is not obvious
3. `Args:` if needed
4. `Returns:` if needed
5. `Raises:` if needed
6. `Examples:` if useful

### Method template

```python
def to_tcl(self) -> str:
    """Render this component as an OpenSees Tcl command.

    Returns:
        Tcl command string for this component.
    """
```

### Method rules

- Every method should have a complete docstring.
- "Complete" means the docstring should document behavior, inputs, outputs, and
  raised errors as needed for that method.
- Do not add empty sections only to satisfy a template.
- `Examples:` are optional for methods.
- If a method example is included and the method belongs to a manager-driven
  Femora workflow, prefer calling it through `model = fm.MeshMaker()` and the
  appropriate manager path when practical.

---

## 7. Example Policy

Class examples are required. Method examples are optional. When examples are
included, they must follow a unified format.

### Required example format

- Always use fenced code blocks:

```python
import femora as fm

model = fm.MeshMaker()
```

- Use `model` as the MeshMaker variable name.
- Prefer `import femora as fm`.
- Use manager-based creation whenever that is the normal Femora API:
  - `model.material...`
  - `model.element...`
  - `model.timeSeries...`
  - `model.groundMotion...`
  - `model.pattern...`
  - other manager entry points as appropriate
- Show realistic dependency creation when tags or manager ownership matter.

### Direct construction rule

Direct class construction is acceptable only when:

- the class is intentionally low-level
- direct construction is the point of the example
- manager-based creation is not the actual public usage path

### Example content rules

- Keep examples short and realistic.
- Do not use fake APIs.
- Do not use placeholder pseudo-code if a real Femora call can be shown.
- Do not use `>>>`.
- Do not include huge outputs unless output is essential.

### Example template

```python
Examples:
    ```python
    import femora as fm

    model = fm.MeshMaker()
    ts = model.timeSeries.path(dt=0.01, filePath="ground.acc")
    pattern = model.pattern.uniform_excitation(dof=1, time_series=ts)
    print(pattern.tag)
    ```
```

---

## 8. Formatting and Indentation

Indentation is critical for automatic parsers.

- Use 4 spaces for the body of each section.
- Wrapped section descriptions should align under the description text with an
  extra 4 spaces.
- Use a blank line after the summary line.
- Use a blank line before each section header.
- Keep indentation consistent inside fenced `python` examples.

### Correct indentation

```python
def example(value: float, other: str):
    """Do something useful.

    Args:
        value: The main numeric value used to create the output. If the
            description wraps, the next line is indented further.
        other: Secondary input.

    Returns:
        Description of the returned value.
    """
```

---

## 9. Section Labels

Use these labels exactly:

- `Args:`
- `Returns:`
- `Raises:`
- `Attributes:`
- `Notes:`
- `Examples:`
- `Tcl form:`

Do not use alternatives such as:

- `Parameters:`
- `Inputs:`
- `Usage:`
- `Example Usage:`
- `Exceptions:`

Consistency matters more than preference.

---

## 10. Explanation Rules

Docstrings should explain the concept behind a class or method when that
context improves understanding.

Examples:

- a class may need a short explanation of what physical or computational idea
  it represents
- a manager method may need a short explanation of what it creates or registers
- a helper method may only need a direct behavior description

Do not add theory for its own sake. Add conceptual explanation only when it
helps the reader understand the code and API.

---

## 11. What AI Must Not Do

When updating docstrings, an AI must not:

- change code logic
- change names
- change signatures
- add fake APIs
- use `>>>`
- add markdown headings inside docstrings
- duplicate constructor `Args:` in both the class docstring and `__init__`
- add `Returns:` to `__init__`
- skip private method docstrings
- write long essays where a short paragraph is enough

---

## 12. AI Review and Rewrite Instructions

Use the following instructions whenever an AI is asked to review or complete
docstrings for a Femora file.

### AI task instructions

1. Review the entire target file before editing.
2. Read related project files when needed to understand managers, base classes,
   usage patterns, or neighboring components.
3. Only modify docstrings in the target file unless explicitly instructed
   otherwise.
4. Preserve all code logic, imports, signatures, names, and behavior.
5. Rewrite existing docstrings to follow this file exactly.
6. Add missing docstrings for all classes and all methods.
7. Every method docstring must be complete, whether the method is public or
   private.
8. Keep class docstrings focused on concept, behavior, Tcl form, notes,
   attributes when useful, and required examples.
9. Keep `__init__` docstrings focused on constructor arguments and validation.
10. Because MkDocs merges `__init__` into the class page, do not duplicate
    constructor `Args:` in the class docstring.
11. Every class must include at least one example.
12. Method examples are optional.
13. If examples are included, use fenced `python` blocks, never `>>>`.
14. If examples are included for normal Femora usage, prefer:

    ```python
    import femora as fm

    model = fm.MeshMaker()
    ```

    and then use manager-based creation when practical.
15. Return the full valid Python file, with no markdown fences around the full
    file.

### Reusable AI prompt

```text
You are editing docstrings for the Femora project.

Follow STYLE_GUIDE.md exactly.

Task:
- Review the entire target file first.
- Read related project files when needed to understand managers, base classes,
  or usage patterns before editing.
- Only change docstrings in the target file.
- Do not change logic, imports, signatures, names, or behavior.
- Rewrite inconsistent docstrings to match the Femora docstring standard.
- Add missing docstrings for all classes and all methods.
- Every method docstring must be complete, whether the method is public or private.
- Keep class docstrings focused on concept, behavior, Tcl form, notes,
  attributes when useful, and required examples.
- Keep __init__ docstrings focused on Args and Raises.
- Because MkDocs merges __init__ into the class page, do not duplicate Args in
  the class docstring.
- Never use >>>.
- Every class must include at least one example.
- Method examples are optional.
- If examples are included, use fenced python blocks.
- If examples are included for normal Femora usage, prefer:
  import femora as fm
  model = fm.MeshMaker()
  and manager-based creation such as model.pattern..., model.timeSeries...,
  model.material..., or other appropriate managers.

Return only the final valid Python code for the full file.
```

---

## 13. AI Checklist

Any human or AI reviewing a docstring update must verify:

1. [ ] Every class has a docstring.
2. [ ] Every method has a docstring, whether public or private.
3. [ ] Class docstrings explain what the class is and does.
4. [ ] `__init__` docstrings document constructor arguments.
5. [ ] No constructor `Args:` are duplicated between the class docstring and
       `__init__`.
6. [ ] `Tcl form:` exists where relevant.
7. [ ] Every class includes at least one example.
8. [ ] Method examples are optional, not required.
9. [ ] If examples are present, they use fenced `python` blocks and not `>>>`.
10. [ ] If examples are present, they prefer real Femora usage through
       `model = fm.MeshMaker()` and manager-based creation when practical.
11. [ ] Section labels match this file exactly.
12. [ ] Wrapped indentation is correct.
13. [ ] No code logic was changed.
