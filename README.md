# Wolverine

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT) 

[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/bio_bootloader.svg?style=social&label=Follow%20%40bio_bootloader)](https://twitter.com/bio_bootloader) [![Downloads](https://static.pepy.tech/badge/wolverine/month)](https://pepy.tech/project/wolverine) 

## 🤔 Why do you need this?

Give your python scripts regenerative healing abilities!

Run your scripts with Wolverine and when they crash, GPT-4 edits them and explains what went wrong. Even if you have many bugs it will repeatedly rerun until it's fixed.

## 🎬 Demonstration
For a quick demonstration see my [video on twitter](https://twitter.com/bio_bootloader/status/1636880208304431104).

## 🛠️ Setup

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.sample .env

Add your openAI api key to `.env`

> :warning: **WARNING** GPT-4 token usage
>
> By default wolverine uses GPT-4 and may make many repeated calls to the api.
>
> :warning: **WARNING** GPT-4 token usage

## 📝 Example Usage

To run with gpt-4 (the default, tested option):

    python wolverine.py buggy_script.py "subtract" 20 3

You can also run with other models, but be warned they may not adhere to the edit format as well:

    python wolverine.py --model=gpt-3.5-turbo buggy_script.py "subtract" 20 3

If you want to use GPT-3.5 by default instead of GPT-4 uncomment the default model line in `.env`:

    DEFAULT_MODEL=gpt-3.5-turbo

You can also use flag `--confirm=True` which will ask you `yes or no` before making changes to the file. If flag is not used then it will apply the changes to the file

    python wolverine.py buggy_script.py "subtract" 20 3 --confirm=True

## 🔮 Future Plans

This is just a quick prototype I threw together in a few hours. There are many possible extensions and contributions are welcome:

- add flags to customize usage, such as asking for user confirmation before running changed code
- further iterations on the edit format that GPT responds in. Currently it struggles a bit with indentation, but I'm sure that can be improved
- a suite of example buggy files that we can test prompts on to ensure reliability and measure improvement
- multiple files / codebases: send GPT everything that appears in the stacktrace
- graceful handling of large files - should we just send GPT relevant classes / functions?
- extension to languages other than python

## 🌟 History

[![Star History Chart](https://api.star-history.com/svg?repos=biobootloader/wolverine&type=Date)](https://star-history.com/#biobootloader/wolverine)

## 💁 Contributing

As an open source project in a rapidly developing field, I am open to contributions, whether it be in the form of a new feature, improved infra, or better documentation.

For detailed information on how to [contribute](.github/CONTRIBUTING.md).
