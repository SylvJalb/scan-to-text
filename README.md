# Scan To Text

Text extraction from scanned images (for exemple handwritten letters) using the **Mistral OCR** model (`mistral-ocr-2512`).

## Prerequisites

- Python >= 3.10
- [Poetry](https://python-poetry.org/docs/#installation)
- A Mistral API key ([console.mistral.ai](https://console.mistral.ai/))
- An OpenAI API key ([platform.openai.com](https://platform.openai.com/)) — for the `--improve` option

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
OPENAI_API_KEY="your_key_here"
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

### Improve OCR results with GPT-5

Once the OCR step is done, you can improve the extracted text by sending it to GPT-5 along with the original scanned image for correction:

```bash
poetry run python main.py --improve
```

For each `.txt` file in `output/`, this will:

1. Find the matching image in `input/`
2. Send both the OCR text and the image to GPT-5 for correction
3. Save the corrected text in `output-improved/` (same filename)

The LLM corrects OCR errors while staying as faithful as possible to the original scan. Uncertain words are marked `[word?]`, and passages that cannot be corrected with confidence are replaced with `[...]` for manual review.

Already improved files are skipped. Use `--force` to reprocess:

```bash
poetry run python main.py --improve --force
```
