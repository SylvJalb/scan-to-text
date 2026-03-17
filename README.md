# OCR Lettres

Text extraction from scanned handwritten letters using the **Mistral OCR** model (`mistral-ocr-2512`).

## Prerequisites

- Python >= 3.10
- [Poetry](https://python-poetry.org/docs/#installation)
- A Mistral API key ([console.mistral.ai](https://console.mistral.ai/))

## Installation

```bash
poetry install
```

## Configuration

Copy the example file and fill in your API key:

```bash
cp .env.exemple .env
```

Edit `.env`:

```
MISTRAL_API_KEY="your_key_here"
```

## Usage

Place your images (`.jpg`, `.jpeg`, `.png`) in the `input/` folder, then run:

```bash
poetry run python main.py
```

Text files will be generated in `output/` with the same name as the source image (e.g. `IMG_0001.jpg` → `IMG_0001.txt`).

### Options

- Already processed images (existing `.txt` file in `output/`) are automatically skipped.
- To **reprocess all images**, add the `--force` flag:

```bash
poetry run python main.py --force
```
