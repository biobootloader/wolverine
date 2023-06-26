# Wolverine

<p align="center">
    
<img alt="Self-healing polymers animation" src="https://github.com/biobootloader/wolverine/assets/5055400/cde545a6-6c63-45ee-9708-275e1ecf09a0" />

</p>

## About

Give your python scripts regenerative healing abilities!

Run your scripts with Wolverine and when they crash, GPT-4 edits them and explains what went wrong. Even if you have many bugs it will repeatedly rerun until it's fixed.

For a quick demonstration see my [demo video on twitter](https://twitter.com/bio_bootloader/status/1636880208304431104).

## Setup

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.sample .env

Add your openAI api key to `.env`

_warning!_ By default wolverine uses GPT-4 and may make many repeated calls to the api.

## Example Usage

To run with gpt-4 (the default, tested option):

    python -m wolverine examples/buggy_script.py "subtract" 20 3

You can also run with other models, but be warned they may not adhere to the edit format as well:

    python -m wolverine --model=gpt-3.5-turbo examples/buggy_script.py "subtract" 20 3

If you want to use GPT-3.5 by default instead of GPT-4 uncomment the default model line in `.env`:

    DEFAULT_MODEL=gpt-3.5-turbo

You can also use flag `--confirm=True` which will ask you `yes or no` before making changes to the file. If flag is not used then it will apply the changes to the file

    python -m wolverine examples/buggy_script.py "subtract" 20 3 --confirm=True

## Environment variables

| env name            | description                                                       | default value |
| ------------------- | ----------------------------------------------------------------- | ------------- |
| OPENAI_API_KEY      | OpenAI API key                                                    | None          |
| DEFAULT_MODEL       | GPT model to use                                                  | "gpt-4"       |
| VALIDATE_JSON_RETRY | Number of retries when requesting OpenAI API (-1 means unlimited) | -1            |

## Future Plans

This is just a quick prototype I threw together in a few hours. There are many possible extensions and contributions are welcome:

- add flags to customize usage, such as asking for user confirmation before running changed code
- further iterations on the edit format that GPT responds in. Currently it struggles a bit with indentation, but I'm sure that can be improved
- a suite of example buggy files that we can test prompts to ensure reliability and measure improvement
- multiple files / codebases: send GPT everything that appears in the stacktrace
- graceful handling of large files &mdash; should we send GPT just the relevant classes / functions?
- extension to languages other than python

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=biobootloader/wolverine&type=Date)](https://star-history.com/#biobootloader/wolverine)

<sup>🌟Graph courtesy of [star-history.com](https://star-history.com/).</sup>

<sup>Gif [fair-use](https://en.wikipedia.org/wiki/Fair_use) derivative of Rowan, SJ (2011) In: _Self-healing polymer fixes scratches._ https://youtu.be/h-fka0wfY8w. Accessed 1 Jun 2023 </sup>
