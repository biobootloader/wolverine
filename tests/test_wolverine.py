import os
import json
import pytest
import tempfile
from wolverine import apply_changes, json_validated_response


@pytest.fixture(scope='function')
def temp_file():
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("first line\nsecond line\nthird line")
    file_path = f.name
    yield file_path
    # Clean up the temporary file
    os.remove(file_path)


def test_apply_changes_replace(temp_file):
    # Make a "replace" change to the second line
    changes = [
        {"operation": "Replace", "line": 2, "content": "new second line"}
    ]
    apply_changes(temp_file, changes)

    # Check that the file was updated correctly
    with open(temp_file) as f:
        content = f.read()
        assert content == "first line\nnew second line\nthird line"


def test_apply_changes_delete(temp_file):
    # Make a "delete" change to the third line
    changes = [
        {"operation": "Delete", "line": 3, "content": ""},
    ]
    apply_changes(temp_file, changes)

    # Check that the file was updated correctly
    with open(temp_file) as f:
        content = f.read()
        assert content == "first line\nsecond line\n"


def test_apply_changes_insert(temp_file):
    # Make an "insert" change after the second line
    changes = [
        {"operation": "InsertAfter", "line": 2, "content": "inserted line"},
    ]
    apply_changes(temp_file, changes)

    # Check that the file was updated correctly
    with open(temp_file) as f:
        content = f.read()
        assert content == 'first line\nsecond line\ninserted line\nthird line'

