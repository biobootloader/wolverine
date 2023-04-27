import os
import pytest
from wolverine import apply_changes, json_validated_response

from .conftest import (
    mock_open_ai_response_object,
    TEST_FILES_DIR
)


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


@pytest.mark.parametrize("chat_completion_response, nb_retry, fail", [
    (os.path.join(TEST_FILES_DIR, "cc_resp.txt"), 3, False),
    (os.path.join(TEST_FILES_DIR, "cc_resp_fail.txt"), 3, True),
    (os.path.join(TEST_FILES_DIR, "cc_resp_fail.txt"), 10, True),
])
def test_json_validated_response(mocker, chat_completion_response, nb_retry, fail):
    # Open the test file
    with open(chat_completion_response, 'r') as file:
        response = file.read()
    # Mock the openAi chat completion API call
    mocker.patch(
        "openai.ChatCompletion.create",
        return_value=mock_open_ai_response_object(mocker=mocker, content=response))
    # ChatCompletion returned an invalid response
    if fail:
        with pytest.raises(Exception) as err:
            json_response = json_validated_response("gpt-4", [
                    {
                        "role": "user",
                        "content": "prompt"
                    }
                ],
                nb_retry=nb_retry
            )
            # Check that the exception is raised after nb_retry time
            assert err.value == "No valid json response found after 3 tries. Exiting."
    else:
        json_response = json_validated_response("gpt-4", [
                {
                    "role": "user",
                    "content": "prompt"
                }
            ],
            nb_retry=nb_retry
        )
        assert json_response
