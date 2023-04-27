"""
Conftest
"""
import os
import pytest
import tempfile


TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")


@pytest.fixture(scope='function')
def temp_file():
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("first line\nsecond line\nthird line")
    file_path = f.name
    yield file_path
    # Clean up the temporary file
    os.remove(file_path)


def mock_open_ai_response_object(mocker, content: str):
    """
    Mocks the response object from the openai api.
    """
    mock_generator_object = mocker.MagicMock()
    mock_message_object = mocker.MagicMock()
    mock_message_object.configure_mock(**{"message.content": content})
    mock_generator_object.configure_mock(**{"choices": [mock_message_object]})
    return mock_generator_object