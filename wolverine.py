import difflib
import fire
import json
import os
import shutil
import subprocess
import sys
import openai
import logging
from termcolor import cprint
from dotenv import load_dotenv
    

    
# Set up the OpenAI API
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gpt-4")


with open("prompt.txt") as f:
    SYSTEM_PROMPT = f.read()
    
# Set up logging
def configure_logging():
    logging.basicConfig(
        filename="wolverine.log",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


# Run the provided script and return the output and return code
def run_script(script_name, script_args):
    script_args = [str(arg) for arg in script_args]
    try:
        result = subprocess.check_output(
            [sys.executable, script_name, *script_args], stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        return e.output.decode("utf-8"), e.returncode
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
    except (json.decoder.JSONDecodeError, ValueError) as e:
        cprint(f"{e}. Re-running the query.", "red")
        # debug
        cprint(f"\nGPT RESPONSE:\n\n{content}\n\n", "yellow")
        # append a user message that says the json is invalid
        messages.append(
            {
                "role": "user",
                "content": "Your response could not be parsed by json.loads. Please restate your last message as pure JSON.",
            }
        )
        # rerun the api call
        return json_validated_response(model, messages)
    except Exception as e:
        cprint(f"Unknown error: {e}", "red")
        cprint(f"\nGPT RESPONSE:\n\n{content}\n\n", "yellow")
        raise e
    return json_response

# Send the error to GPT and receive suggestions
def send_error_to_gpt(file_path, args, error_message, model=DEFAULT_MODEL, prompt_length_limit=4096):
    with open(file_path, "r") as f:
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

    # Truncate the prompt if it exceeds the limit
    if len(prompt) > prompt_length_limit:
        prompt = prompt[:prompt_length_limit]
        
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
    
# Apply the changes suggested by GPT
def apply_changes(file_path, changes: list):
    """
    Pass changes as loaded json (list of dicts)
    """
    try:
        with open(file_path, "r") as f:
            original_file_lines = f.readlines()

        operation_changes = [change for change in changes if "operation" in change]
        explanations = [
            change["explanation"] for change in changes if "explanation" in change
        ]

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
        print_diff(original_file_lines, file_lines)
    except Exception as e:
        raise Exception(f"Failed to apply changes: {str(e)}")
    
# Apply a single change suggested by GPT interactively
def apply_change_interactive(file_path, change):
    with open(file_path, "r") as f:
        original_file_lines = f.readlines()

    operation = change["operation"]
    line = change["line"]
    content = change["content"]

    file_lines = original_file_lines.copy()
    if operation == "Replace":
        file_lines[line - 1] = content + "\n"
    elif operation == "Delete":
        del file_lines[line - 1]
    elif operation == "InsertAfter":
        file_lines.insert(line, content + "\n")

    print("\nSuggested change:")
    print_diff(original_file_lines, file_lines)

    while True:
        decision = input("Do you want to apply this change? (y/n): ").lower()
        if decision == "y":
            with open(file_path, "w") as f:
                f.writelines(file_lines)
            logging.info(f"Applied change: {change}")
            return True
        elif decision == "n":
            logging.info(f"Rejected change: {change}")
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

# Print the differences between two file contents
def print_diff(original_file_lines, file_lines):
    diff = difflib.unified_diff(original_file_lines, file_lines, lineterm="")
    for line in diff:
        if line.startswith("+"):
            cprint(line, "green", end="")
        elif line.startswith("-"):
            cprint(line, "red", end="")
        else:
            print(line, end="")

def main(script_name, *script_args, revert=False, model=DEFAULT_MODEL, interactive=False):
    if revert:
        backup_file = script_name + ".bak"
        if os.path.exists(backup_file):
            shutil.copy(backup_file, script_name)
            print(f"Reverted changes to {script_name}")
            return
        else:
            raise Exception(f"No backup file found for {script_name}")

    # Make a backup of the original script
    shutil.copy(script_name, script_name + ".bak")

    while True:
        output, returncode = run_script(script_name, script_args)

        if returncode == 0:
            cprint("Script ran successfully.", "blue")
            print("Output:", output)
            logging.info("Script ran successfully.")
            break
        else:
            cprint("Script crashed. Trying to fix...", "blue")
            logging.error(f"Script crashed with return code {returncode}.")
            print("Output:", output)

            json_response = send_error_to_gpt(
                file_path=script_name,
                args=script_args,
                error_message=output,
                model=model,
            )
            if interactive:
                changes = json_response
                operation_changes = [change for change in changes if "operation" in change]
                explanations = [
                    change["explanation"] for change in changes if "explanation" in change
                ]

                for change in operation_changes:
                    if apply_change_interactive(script_name, change):
                        cprint("Change applied.", "green")
                    else:
                        cprint("Change rejected.", "red")
                cprint("Finished applying changes. Rerunning...", "blue")
                logging.info("Finished applying changes in interactive mode.")
            else:
                try:
                    apply_changes(script_name, json_response)
                    cprint("Changes applied. Rerunning...", "blue")
                    logging.info("Changes applied.")
                except Exception as e:
                    raise Exception(f"Failed to fix the script: {str(e)}")


if __name__ == "__main__":
    configure_logging()
    try:
        fire.Fire(main)
    except Exception as e:
        print(str(e))
        logging.error(f"Error: {str(e)}")
        sys.exit(1)

