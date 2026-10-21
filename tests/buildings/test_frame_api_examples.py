"""Keep public API snippets executable and constructor parameters documented."""
import inspect
import re

from femora.tools.buildings import SteelConcentricallyBracedFrame3D
from femora.tools.sections import aisc


def test_all_constructor_parameters_documented():
    doc = inspect.getdoc(SteelConcentricallyBracedFrame3D.__init__)
    for name in inspect.signature(SteelConcentricallyBracedFrame3D).parameters:
        assert re.search(r"^\s+" + name + r":", doc, re.MULTILINE), name


def test_building_class_examples_execute():
    namespace = {}
    for snippet in re.findall(r"```python\n(.*?)```", inspect.getdoc(SteelConcentricallyBracedFrame3D), re.DOTALL):
        exec(compile(inspect.cleandoc(snippet), "building_api_example", "exec"), namespace)
    assert namespace["frame"].section_factory is namespace["custom_section"]


def test_aisc_examples_execute():
    namespace = {}
    for snippet in re.findall(r"```python\n(.*?)```", inspect.getdoc(aisc.create_section), re.DOTALL):
        exec(compile(inspect.cleandoc(snippet), "aisc_api_example", "exec"), namespace)
    assert len(namespace["fine"].patches) == 3
    assert namespace["fiber"].get_area() == namespace["fine"].get_area()
