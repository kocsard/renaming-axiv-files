# Renaming ArXiv Files

Automatically rename PDF files downloaded from arXiv to the format `Author - Title.pdf`.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Rename a single file
python rename_arxiv.py ~/Downloads/2304.00001.pdf

# Rename multiple files
python rename_arxiv.py ~/Downloads/*.pdf
```

## Supported arXiv ID Formats

| Format | Example |
|---|---|
| New-style | `2304.00001.pdf`, `2304.00001v2.pdf` |
| Old-style | `hep-th0601001.pdf`, `math.AG0601001v1.pdf` |

## Naming Convention

| Authors | Format |
|---|---|
| 1 author | `LastName - Title.pdf` |
| 2 authors | `LastName1, LastName2 - Title.pdf` |
| 3+ authors | `LastName1 et al. - Title.pdf` |

## Dependencies

- Python 3.9+
- [requests](https://pypi.org/project/requests/)