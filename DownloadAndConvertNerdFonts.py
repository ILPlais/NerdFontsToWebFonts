#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
download_and_convert_nerd_fonts.py

Download font families from the official Nerd Fonts repository
(https://github.com/ryanoasis/nerd-fonts) and convert their .ttf files
to .woff2, ready for use on the Web.

Single dependency (downloads use urllib from the standard library):
	pip install --user "fonttools[woff]"

Examples:
	# List available families in the latest release
	python3 download_and_convert_nerd_fonts.py --list-families

	# Download and convert two specific families
	python3 download_and_convert_nerd_fonts.py --families JetBrainsMono FiraCode --output-dir ./fonts

	# Target a specific version instead of the latest release
	python3 download_and_convert_nerd_fonts.py --tag v3.5.1 --families Hack

	# Download and convert everything (this can take a while!)
	python3 download_and_convert_nerd_fonts.py --output-dir ./fonts
"""

import argparse
import io
import json
import os
import pathlib
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

from fontTools.ttLib.woff2 import compress

# 🌐 GitHub API root for the official Nerd Fonts repository
GITHUB_API_ROOT = "https://api.github.com/repos/ryanoasis/nerd-fonts"

# GitHub requires a User-Agent on every API request
USER_AGENT = "nerd-fonts-woff2-converter"


def fetch_release(tag = None, github_token = None):
	"""
	Fetch JSON metadata for a Nerd Fonts GitHub release.

	If `tag` is None, the latest release is used.
	An optional GitHub token avoids the anonymous rate limit (60/hour).
	"""
	if tag:
		url = f"{GITHUB_API_ROOT}/releases/tags/{tag}"
	else:
		url = f"{GITHUB_API_ROOT}/releases/latest"

	headers = {'Accept': "application/vnd.github+json", 'User-Agent': USER_AGENT}
	if github_token:
		headers['Authorization'] = f"Bearer {github_token}"

	request = urllib.request.Request(url, headers = headers)

	try:
		with urllib.request.urlopen(request, timeout = 30) as response:
			return json.load(response)
	except urllib.error.HTTPError as error:
		print(f"❌ Unable to fetch the release ({error.code}): {url}")
		sys.exit(1)


def list_font_assets(release):
	"""
	Filter release assets to keep only .zip archives that correspond to
	font families (skip ancillary files such as checksums).
	"""
	return [asset for asset in release['assets'] if asset['name'].endswith(".zip")]


def download_and_extract(asset, destination_dir):
	"""
	Download a font family's .zip archive and extract every .ttf file
	into `destination_dir`.

	Returns the list of extracted .ttf file paths.
	"""
	print(f"📥 Downloading {asset['name']}...")

	request = urllib.request.Request(
		asset['browser_download_url'],
		headers = {'User-Agent': USER_AGENT},
	)
	with urllib.request.urlopen(request, timeout = 120) as response:
		archive_bytes = response.read()

	extracted_files = []
	with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
		for member in archive.namelist():
			if member.lower().endswith((".ttf", ".otf")):
				archive.extract(member, path = destination_dir)
				extracted_files.append(destination_dir / member)

	return extracted_files


def convert_to_woff2(ttf_path, output_dir):
	"""
	Convert a .ttf or .otf file to .woff2 with fontTools, and write the result
	into `output_dir` while keeping the original file stem.
	"""
	woff2_path = output_dir / f"{ttf_path.stem}.woff2"
	compress(input_file = str(ttf_path), output_file = str(woff2_path))
	return woff2_path


def process_family(family_name, asset, output_root):
	"""
	Download, extract, then convert every .ttf or .otf font in a given family.
	WOFF2 files go into a subdirectory named after the family;
	intermediate files are not kept.
	"""
	family_output_dir = output_root / family_name
	family_output_dir.mkdir(parents = True, exist_ok = True)

	with tempfile.TemporaryDirectory() as tmp_dir_name:
		tmp_dir = pathlib.Path(tmp_dir_name)
		ttf_files = download_and_extract(asset = asset, destination_dir = tmp_dir)

		if not ttf_files:
			print(f"⚠️  No .ttf or .otf font found in {asset['name']}")
			return

		print(f"🔣 {len(ttf_files)} font{'s' if len(ttf_files) != 1 else ''} to convert for {family_name}")

		for ttf_path in ttf_files:
			woff2_path = convert_to_woff2(ttf_path = ttf_path, output_dir = family_output_dir)
			print(f"   ✅ {ttf_path.name} → {woff2_path.relative_to(output_root)}")


def main():
	parser = argparse.ArgumentParser(
		description = "Download and convert Nerd Fonts families to WOFF2.",
	)
	parser.add_argument(
		"--families",
		nargs = "+",
		metavar = "NAME",
		help = "Family name(s) to process (e.g. JetBrainsMono FiraCode). "
		       "If omitted, ALL families in the release are processed.",
	)
	parser.add_argument(
		"--tag",
		default = None,
		help = "Nerd Fonts release tag to use (e.g. v3.5.1). "
		       "Default: latest release.",
	)
	parser.add_argument(
		"--output-dir",
		default = "./nerd-fonts-woff2",
		help = "Destination directory for converted fonts.",
	)
	parser.add_argument(
		"--list-families",
		action = "store_true",
		help = "Print the list of available families and exit, without downloading anything.",
	)
	parser.add_argument(
		"--github-token",
		default = os.environ.get("GITHUB_TOKEN"),
		help = "Optional GitHub token (or GITHUB_TOKEN environment variable) "
		       "to avoid the API anonymous rate limit.",
	)

	args = parser.parse_args()

	print("🔎 Fetching Nerd Fonts release information...")
	release = fetch_release(tag = args.tag, github_token = args.github_token)
	font_assets = list_font_assets(release = release)

	if args.list_families:
		print(f"📦 Release {release['tag_name']} — {len(font_assets)} available family/families:\n")
		for asset in sorted(font_assets, key = lambda item: item['name']):
			print(f"   • {pathlib.Path(asset['name']).stem}")
		return

	# Build a {family_name: asset} dictionary for easy lookup
	assets_by_family = {pathlib.Path(asset['name']).stem: asset for asset in font_assets}

	requested_families = args.families or list(assets_by_family.keys())
	output_root = pathlib.Path(args.output_dir)
	output_root.mkdir(parents = True, exist_ok = True)

	for family_name in requested_families:
		asset = assets_by_family.get(family_name)
		if asset is None:
			print(f"❌ Unknown family: {family_name} (try --list-families)")
			continue

		process_family(family_name = family_name, asset = asset, output_root = output_root)

	print(f"\n🎉 Done! Converted fonts are in {output_root}")


if __name__ == "__main__":
	main()
