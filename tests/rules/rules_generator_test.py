import pytest
import glob

from norminette.context import Context
from norminette.registry import Registry
from norminette.file import File


registry = Registry()
test_files = glob.glob("tests/rules/samples/*.[ch]")


@pytest.mark.parametrize("file", test_files)
def test_rule_for_file(file, capsys):
    with open(file, "r") as test_file:
        file = File(file, test_file.read())

    with open(f"{file.path[:-2]}.out") as out_file:
        out_content = out_file.read()

    context = Context(file, debug=2)
    registry.run(context)
    captured = capsys.readouterr()

    assert captured.out == out_content
