import difflib
import fire
import json
import os
import shutil
import subprocess
import sys

import openai
from termcolor import cprint

# Set up the OpenAI API
with open("openai_key.txt") as f:
    openai.api_key = f.read().strip()

def run_script(script_name, script_args):
    script_args = [str(arg) for arg in script_args]
    try:
        result = subprocess.check_output(
            [sys.executable, script_name, *script_args], stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        return e.output.decode("utf-8"), e.returncode
    return result.decode("utf-8"), 0


def send_error_to_gpt(file_path, args, error_message, model):
    with open(file_path, "r") as f:
        file_lines = f.readlines()

    file_with_lines = []
    for i, line in enumerate(file_lines):
        file_with_lines.append(str(i + 1) + ": " + line)
    file_with_lines = "".join(file_with_lines)

    with open("prompt.txt") as f:
        initial_prompt_text = f.read()

    prompt = (
        initial_prompt_text +
        "\n\n"
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

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=1.0,
    )

    return response.choices[0].message.content.strip()


def apply_changes(file_path, changes_json):
    with open(file_path, "r") as f:
        original_file_lines = f.readlines()

    changes = json.loads(changes_json)

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

    with open(file_path, "w") as f:
        f.writelines(file_lines)

    # Print explanations
    cprint("Explanations:", "blue")
    for explanation in explanations:
        cprint(f"- {explanation}", "blue")

    # Show the diff
    print("\nChanges:")
    diff = difflib.unified_diff(original_file_lines, file_lines, lineterm="")
    for line in diff:
        if line.startswith("+"):
            cprint(line, "green", end="")
        elif line.startswith("-"):
            cprint(line, "red", end="")
        else:
            print(line, end="")

def avaibility(openaiObj):
    models_available = [x['id'] for x in openai.Model.list()['data']]
    if "gpt-4" not in models_available:
        model = "gpt-3.5-turbo"
    else:
        model = "gpt-4"
    return model



def main(script_name, *script_args, revert=False):
    model = avaibility(openai)
    if revert:
        backup_file = script_name + ".bak"
        if os.path.exists(backup_file):
            shutil.copy(backup_file, script_name)
            print(f"Reverted changes to {script_name}")
            sys.exit(0)
        else:
            print(f"No backup file found for {script_name}")
            sys.exit(1)

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
            apply_changes(script_name, json_response)
            cprint("Changes applied. Rerunning...", "blue")


if __name__ == "__main__":
    fire.Fire(main)

