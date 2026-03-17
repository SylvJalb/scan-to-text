import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mistralai.client import Mistral

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
MODEL = "mistral-ocr-2512"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def encode_image_base64(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("utf-8")


def get_mime_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    return "application/octet-stream"


def get_images(input_dir: Path) -> list[Path]:
    return sorted(
        p
        for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def main() -> None:
    load_dotenv()

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY not set in .env file")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    images = get_images(INPUT_DIR)
    if not images:
        print(f"No images found in {INPUT_DIR}/")
        sys.exit(0)

    total = len(images)
    print(f"Found {total} image(s) in {INPUT_DIR}/")

    # Skip already processed files
    skip_existing = "--force" not in sys.argv
    skipped = 0

    with Mistral(api_key=api_key) as client:
        for i, image_path in enumerate(images, start=1):
            output_path = OUTPUT_DIR / f"{image_path.stem}.txt"

            if skip_existing and output_path.exists():
                skipped += 1
                continue

            print(f"[{i}/{total}] {image_path.name} ... ", end="", flush=True)

            try:
                b64_data = encode_image_base64(image_path)
                mime = get_mime_type(image_path)
                data_uri = f"data:{mime};base64,{b64_data}"

                response = client.ocr.process(
                    model=MODEL,
                    document={
                        "type": "image_url",
                        "image_url": data_uri,
                    },
                )

                text = "\n\n".join(page.markdown for page in response.pages)
                output_path.write_text(text, encoding="utf-8")
                print("OK")

            except Exception as e:
                print(f"ERROR: {e}")

    if skipped:
        print(
            f"{skipped} file(s) skipped (already processed, use --force to reprocess)"
        )

    print("Done.")


if __name__ == "__main__":
    main()
