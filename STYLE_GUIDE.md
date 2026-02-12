# Femora Docstring Standard (Google Style)

This document serves as the **SINGLE SOURCE OF TRUTH** for all docstrings in the Femora project.

**Location**: This file is located at the **Root** of the repository (`STYLE_GUIDE.md`) to be easily accessible to all contributors and agents. It governs the documentation standards for `src/femora`.

---

## 1. Class vs. Constructor (`__init__`)

A common point of confusion is "Where do I document attributes vs. arguments?".

### Rule:
*   **Class Docstring**: Documents **WHAT** the class is and its **Attributes** (state stored in `self`).
*   **`__init__` Docstring**: Documents **HOW** to create the class and its **Arguments** (parameters passed to `__init__`).

### Template:

```python
class BeamElement:
    """Represents a finite element beam in the structural model.
    <BLANK LINE>
    This class handles the geometric transformation and stiffness matrix
    calculations for Euler-Bernoulli beams.
    <BLANK LINE>
    Attributes:
        tag (int): The unique identifier for this element.
        nodes (list[int]): The tags of the two connected nodes [i, j].
        length (float): The calculated length of the beam.
        section (Section): The associated cross-section object.
    """

    def __init__(self, tag: int, nodes: list[int], section: Section = None):
        """Initializes the BeamElement.
        <BLANK LINE>
        Args:
            tag: The unique integer ID for the element.
            nodes: A list of exactly two integer node tags [i-node, j-node].
            section: Optional. The cross-section property. If None, a default
                elastic section is assigned.
        <BLANK LINE>
        Raises:
            ValueError: If `nodes` does not contain exactly 2 integers.
        """
        self.tag = tag
        self.nodes = nodes
        # ... logic ...
```

---

## 2. Indentation & Formatting

Indentation is **critical** for automatic parsers (Mintlify/MKDocs).

*   **Indent**: Use **4 spaces** for the body of sections (Args, Returns, etc.).
*   **Colon**: Use `Name: Description` syntax in `Args`. Do **NOT** put types in parentheses in `Args` if using type hints in the signature (Redundancy Rule).
*   **Continuation**: If a description wraps to the next line, indent it by **another 4 spaces** (total 8 from margin).

### Correct Indentation:

```python
    Args:
        density: The target density of the mesh. This value is used to
            calculate the average element size. (Note the extra indent here)
        material_type: The name of the material.
```

---

## 3. Examples Section

**Requirement**: Every **Public** class and "complex" public method **MUST** have an `Example` section.

*   Use `>>>` (REPL style) for code blocks.
*   Shows the user exactly how to import and use it.

### Template:

```python
    """
    ... (Summaries) ...

    Example:
        >>> import femora as fm
        >>> beam = fm.BeamElement(tag=1, nodes=[10, 20])
        >>> print(beam.length)
        5.0
    """
```

---

## 4. The "Checklist" for AI Agents

Any Agent working on this codebase must verify:

1.  [ ] **Class Docstring**: Has `Attributes` section? (NOT `Args`).
2.  [ ] **Init Docstring**: Has `Args` section? (NOT `Attributes`).
3.  [ ] **Type Hints**: Are they in the signature `def foo(x: int):`? (If yes, omit `(int)` in docstring).
4.  [ ] **Blank Lines**: Is there a blank line after the summary and before section headers?
5.  [ ] **Example**: Is there a working `Example` block for this public component?
