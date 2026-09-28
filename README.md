# NerdFontsToWebFonts

Convert the [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) TTF and OTF files to WOFF2.

## Installation

### Create your virtual environment

**Under Linux or macOS:**

```bash
python3 -m venv .venv
```

**Under Windows:**

```powershell
python -m venv .venv
```

### Switch on your new virtual environment

**Under Linux or macOS:**

```bash
source .venv/bin/activate
```

**Under Windows:**

- In **PowerShell**:

	```powershell
	.\.venv\Scripts\Activate.ps1
	```

- In **Command Prompt**:

	```batch
	.venv\Scripts\activate.bat
	```

### Install packages

You need some Python packages to run the scripts. Install them with **pip**:

```bash
pip install --require-virtualenv --requirement=requirements.txt
```

## Usage

```
usage: DownloadAndConvertNerdFonts.py [-h] [--families NAME [NAME ...]] [--tag TAG] [--output-dir OUTPUT_DIR]
                                      [--list-families] [--github-token GITHUB_TOKEN]

Download and convert Nerd Fonts families to WOFF2.

options:
  -h, --help            show this help message and exit
  --families NAME [NAME ...]
                        Family name(s) to process (e.g. JetBrainsMono FiraCode). If omitted, ALL families in the
                        release are processed.
  --tag TAG             Nerd Fonts release tag to use (e.g. v3.5.1). Default: latest release.
  --output-dir OUTPUT_DIR
                        Destination directory for converted fonts.
  --list-families       Print the list of available families and exit, without downloading anything.
  --github-token GITHUB_TOKEN
                        Optional GitHub token (or GITHUB_TOKEN environment variable) to avoid the API anonymous rate
                        limit.
```
