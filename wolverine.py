import difflib
import json
import os
import shutil
import subprocess
import sys

import openai
from dotenv import load_dotenv
from termcolor import cprint

"""
Relevants models, more can be added
"""
RELEVANT = ["gpt-3.5-turbo", "text-davinci-003", "text-davinci-002", "code-davinci-002"]


def get_api_key():
    """
    Ask for the openAI key in command line if not set in .env
    """
    global DEFAULT_MODEL, AVAILABLE_MODELS
    load_dotenv()
    if (os.getenv("OPENAI_API_KEY") == "your-api-key-here"):
        load_dotenv()
        key = input("Paste your openAI API key, or put it in the .env file:\n->")
        os.environ["OPENAI_API_KEY"] = key
    openai.api_key = os.getenv("OPENAI_API_KEY")


get_api_key()
AVAILABLE_MODELS = [x['id'] for x in openai.Model.list()["data"]]
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gpt-4" if "gpt-4" in AVAILABLE_MODELS else "gpt-3.5-turbo")

def check_model_availability(model):
    if model not in AVAILABLE_MODELS:
        print(f"Model {model} is not available.Please try with another model. You can also configure a " "default model in the .env")
        return False
    return True


def model_choice(model):
    """
    Ask for which model to choose in command line
    """
    global DEFAULT_MODEL
    models = [_ for _ in AVAILABLE_MODELS if _ in RELEVANT]
    if (input(f"default model: {model}\nContinue? n to choose another model [y/n]") == 'n'):
        while (1):
            model_chose = input(f"Also available: {models}:\nWrite the model you want to chose ->")
            DEFAULT_MODEL = model_chose
            if (check_model_availability(DEFAULT_MODEL)):
                print(f"Succesfully switched to {DEFAULT_MODEL}")
                break

model_choice(DEFAULT_MODEL)


with open("../prompt.txt", encoding="utf-8") as file:
    SYSTEM_PROMPT = file.read()


def run_script(script_name, script_args):
    """
    If script_name.endswith(".py") then run with python
    else run with node
    """
    script_args = [str(arg) for arg in script_args]
    subprocess_args = (
        [sys.executable, script_name, *script_args]
        if script_name.endswith(".py")
        else ["node", script_name, *script_args]
    )

    try:
        result = subprocess.check_output(
            subprocess_args,
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as error:
        return error.output.decode("utf-8"), error.returncode
    return result.decode("utf-8"), 0


def json_validated_response(model, messages):
    """
    This function is needed because the API can return a non-json response.
    This will run recursively until a valid json response is returned.
    todo: might want to stop after a certain number of retries
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.5,
    )
    messages.append(response.choices[0].message)
    content = response.choices[0].message.content
    # see if json can be parsed
    try:
        json_start_index = content.index(
            "["
        )  # find the starting position of the JSON data
        json_data = content[
            json_start_index:
        ]  # extract the JSON data from the response string
        json_response = json.loads(json_data)
    except (json.decoder.JSONDecodeError, ValueError) as error:
        cprint(f"{error}. Re-running the query.", "red")
        # debug
        cprint(f"\nGPT RESPONSE:\n\n{content}\n\n", "yellow")
        # append a user message that says the json is invalid
        messages.append(
            {
                "role": "user",
                "content": (
                    "Your response could not be parsed by json.loads. "
                    "Please restate your last message as pure JSON."
                ),
            }
        )
        # rerun the api call
        return json_validated_response(model, messages)
    except Exception as error:
        cprint(f"Unknown error: {error}", "red")
        cprint(f"\nGPT RESPONSE:\n\n{content}\n\n", "yellow")
        raise error
    return json_response


def send_error_to_gpt(file_path, args, error_message, model=DEFAULT_MODEL):
    with open(file_path) as f:
        file_lines = f.readlines()

    file_with_lines = []
    for i, line in enumerate(file_lines):
        file_with_lines.append(str(i + 1) + ": " + line)
    file_with_lines = "".join(file_with_lines)

    prompt = (
        "Here is the script that needs fixing:\n\n"
        f"{file_with_lines}\n\n"
        "Here are the arguments it was provided:\n\n"
        f"{args}\n\n"
        "Here is the error message:\n\n"
        f"{error_message}\n"
        "Please provide your suggested changes, and remember to stick to the "
        "exact format as described above."
    )

    # print(prompt)
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    return json_validated_response(model, messages)


def apply_changes(file_path, changes: list, confirm=False):
    """
    Pass changes as loaded json (list of dicts)
    """
    with open(file_path) as f:
        original_file_lines = f.readlines()

    # Filter out explanation elements
    operation_changes = [change for change in changes if "operation" in change]
    explanations = [
        change["explanation"] for change in changes if "explanation" in change
    ]

    # Sort the changes in reverse line order
    operation_changes.sort(key=lambda x: x["line"], reverse=True)

    file_lines = original_file_lines.copy()
    for change in operation_changes:
        operation = change["operation"]
        line = change["line"]
        content = change["content"]

        if operation == "Replace":
            file_lines[line - 1] = content + "\n"
        elif operation == "Delete":
            del file_lines[line - 1]
        elif operation == "InsertAfter":
            file_lines.insert(line, content + "\n")

    # Print explanations
    cprint("Explanations:", "blue")
    for explanation in explanations:
        cprint(f"- {explanation}", "blue")

    # Display changes diff
    print("\nChanges to be made:")
    diff = difflib.unified_diff(original_file_lines, file_lines, lineterm="")
    for line in diff:
        if line.startswith("+"):
            cprint(line, "green", end="")
        elif line.startswith("-"):
            cprint(line, "red", end="")
        else:
            print(line, end="")

    if confirm:
        # check if user wants to apply changes or exit
        confirmation = input("Do you want to apply these changes? (y/n): ")
        if confirmation.lower() != "y":
            print("Changes not applied")
            sys.exit(0)

    with open(file_path, "w") as f:
        f.writelines(file_lines)
    print("Changes applied.")


def main(script_name, *script_args, revert=False, model=DEFAULT_MODEL, confirm=False):
    if revert:
        backup_file = script_name + ".bak"
        if os.path.exists(backup_file):
            shutil.copy(backup_file, script_name)
            print(f"Reverted changes to {script_name}")
            sys.exit(0)
        else:
            print(f"No backup file found for {script_name}")
            sys.exit(1)

    # check if model is available
    check_model_availability(model)

    # Make a backup of the original script
    shutil.copy(script_name, script_name + ".bak")

    while True:
        output, returncode = run_script(script_name, script_args)

        if returncode == 0:
            cprint("Script ran successfully.", "blue")
            print("Output:", output)
            break

        else:
            cprint("Script crashed. Trying to fix...", "blue")
            print("Output:", output)
            json_response = send_error_to_gpt(
                file_path=script_name,
                args=script_args,
                error_message=output,
                model=model,
            )

            apply_changes(script_name, json_response, confirm=confirm)
            cprint("Changes applied. Rerunning...", "blue")
