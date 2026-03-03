#!/usr/bin/env python3
"""
Rename PDF files downloaded from arXiv to the format:
    Author - Title.pdf

Usage:
    python rename_arxiv.py <file1.pdf> [file2.pdf ...]

Supported arXiv filename patterns:
    - New-style IDs:  2304.00001.pdf, 2304.00001v2.pdf
    - Old-style IDs:  hep-th0601001.pdf, math.AG0601001v1.pdf
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

import requests

# ArXiv Atom API endpoint
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# Regex patterns for arXiv IDs embedded in filenames
NEW_STYLE_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")
OLD_STYLE_RE = re.compile(r"([a-z\-]+(?:\.[A-Z]{2})?(\d{7}))(v\d+)?")

def extract_arxiv_id(filename: str) -> str | None:
    """Extract an arXiv ID from a PDF filename.

    Returns the canonical ID (without version suffix) or None.
    """
    basename = os.path.splitext(os.path.basename(filename))[0]

    match = NEW_STYLE_RE.search(basename)
    if match:
        return match.group(1)

    match = OLD_STYLE_RE.search(basename)
    if match:
        return match.group(1)

    return None

def fetch_metadata(arxiv_id: str) -> dict:
    """Query the arXiv Atom API and return title + author list.

    Returns:
        {"title": str, "authors": [str, ...]}

    Raises:
        RuntimeError on network / parsing errors.
    """
    response = requests.get(
        ARXIV_API_URL,
        params={"id_list": arxiv_id, "max_results": "1"},
        timeout=30,
    )
    response.raise_for_status()

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(response.text)
    entry = root.find("atom:entry", ns)
    if entry is None:
        raise RuntimeError(f"No entry found for arXiv ID {arxiv_id}")

    title_el = entry.find("atom:title", ns)
    if title_el is None or not title_el.text:
        raise RuntimeError(f"No title found for arXiv ID {arxiv_id}")

    title = " ".join(title_el.text.split())  # collapse whitespace / newlines

    authors = []
    for author_el in entry.findall("atom:author", ns):
        name_el = author_el.find("atom:name", ns)
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    if not authors:
        raise RuntimeError(f"No authors found for arXiv ID {arxiv_id}")

    return {"title": title, "authors": authors}

def last_name(full_name: str) -> str:
    """Return a best-effort last name from a full name string."""
    parts = full_name.strip().split()
    return parts[-1] if parts else full_name

def build_author_string(authors: list[str]) -> str:
    """Format the author part of the filename.

    1 author  -> LastName
    2 authors -> LastName1, LastName2
    3+ authors -> LastName1 et al.
    """
    if len(authors) == 1:
        return last_name(authors[0])
    if len(authors) == 2:
        return f"{last_name(authors[0])}, {last_name(authors[1])}"
    return f"{last_name(authors[0])} et al."

def sanitize(text: str) -> str:
    """Remove or replace characters that are problematic in filenames."""
    # Replace colons, slashes, etc. with a hyphen; strip leading/trailing spaces
    text = re.sub(r'[\\/:*?"<>|]', "-", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def rename_file(filepath: str, dry_run: bool = False) -> str | None:
    """Rename a single arXiv PDF. Returns the new path or None on skip."""
    arxiv_id = extract_arxiv_id(filepath)
    if arxiv_id is None:
        print(f"  SKIP  {filepath}  (could not detect arXiv ID)")
        return None

    print(f"  arXiv ID: {arxiv_id}")

    metadata = fetch_metadata(arxiv_id)
    author_str = build_author_string(metadata["authors"])
    title = sanitize(metadata["title"])
    new_name = f"{author_str} - {title}.pdf"

    directory = os.path.dirname(filepath) or "."
    new_path = os.path.join(directory, new_name)

    if os.path.abspath(filepath) == os.path.abspath(new_path):
        print(f"  Already named correctly: {new_name}")
        return new_path

    if os.path.exists(new_path):
        print(f"  WARNING  Target already exists, skipping: {new_path}")
        return None

    if dry_run:
        print(f"  DRY RUN  {os.path.basename(filepath)} -> {new_name}")
    else:
        os.rename(filepath, new_path)
        print(f"  RENAMED  {os.path.basename(filepath)} -> {new_name}")

    return new_path

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Rename arXiv PDF files to 'Author - Title.pdf'."
    )
    parser.add_argument("files", nargs="+", help="PDF files to rename")
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually renaming",
    )
    args = parser.parse_args()

    for filepath in args.files:
        if not os.path.isfile(filepath):
            print(f"  ERROR  Not a file: {filepath}")
            continue
        try:
            rename_file(filepath, dry_run=args.dry_run)
        except Exception as exc:
            print(f"  ERROR  {filepath}: {exc}")

if __name__ == "__main__":
    main()