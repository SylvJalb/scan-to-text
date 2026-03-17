import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mistralai.client import Mistral
from openai import OpenAI

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
OUTPUT_IMPROVED_DIR = Path("output-improved")
MODEL = "mistral-ocr-2512"
LLM_MODEL = "gpt-5"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

SYSTEM_PROMPT = """Tu es un expert en correction de textes anciens numérisés par OCR.
Tu reçois un texte extrait par OCR ainsi que l'image scannée originale correspondante.

Ta mission est de corriger le texte OCR en te référant à l'image scannée.

Règles strictes :
- Reste le plus fidèle possible au texte original tel qu'il apparaît sur le scan.
- Si un mot est trop incertain, indique-le ainsi : [?]
- Si une phrase est incohérente à cause d'une erreur OCR, corrige-la selon le contexte tout en restant fidèle au scan.
- Si tu as un trop gros doute sur un passage (complètement incohérant) et que tu ne peux pas le corriger avec confiance, marque "[...]" à la place. L'utilisateur le corrigera manuellement plus tard.
- Ta réponse doit contenir UNIQUEMENT le texte corrigé. Aucune explication, aucun commentaire, aucune introduction, aucune conclusion."""


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


def find_image_for_text(stem: str) -> Path | None:
    for ext in IMAGE_EXTENSIONS:
        candidate = INPUT_DIR / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def improve_texts() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set in .env file")
        sys.exit(1)

    OUTPUT_IMPROVED_DIR.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(OUTPUT_DIR.glob("*.txt"))
    if not txt_files:
        print(f"No text files found in {OUTPUT_DIR}/")
        sys.exit(0)

    total = len(txt_files)
    print(f"Found {total} text file(s) in {OUTPUT_DIR}/")

    skip_existing = "--force" not in sys.argv
    skipped = 0

    client = OpenAI(api_key=api_key)

    for i, txt_path in enumerate(txt_files, start=1):
        improved_path = OUTPUT_IMPROVED_DIR / txt_path.name

        if skip_existing and improved_path.exists():
            skipped += 1
            continue

        image_path = find_image_for_text(txt_path.stem)
        if not image_path:
            print(f"[{i}/{total}] {txt_path.name} ... SKIP (no matching image)")
            continue

        print(f"[{i}/{total}] {txt_path.name} ... ", end="", flush=True)

        try:
            ocr_text = txt_path.read_text(encoding="utf-8")
            b64_data = encode_image_base64(image_path)
            mime = get_mime_type(image_path)
            data_uri = f"data:{mime};base64,{b64_data}"

            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": data_uri},
                            },
                            {
                                "type": "text",
                                "text": f"Voici le texte OCR à corriger :\n\n{ocr_text}",
                            },
                        ],
                    },
                ],
            )

            corrected = response.choices[0].message.content
            improved_path.write_text(corrected, encoding="utf-8")
            print("OK")

        except Exception as e:
            print(f"ERROR: {e}")

    if skipped:
        print(f"{skipped} file(s) skipped (already improved, use --force to reprocess)")

    print("Done.")


def run_ocr() -> None:
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


def main() -> None:
    load_dotenv()

    if "--improve" in sys.argv:
        improve_texts()
    else:
        run_ocr()


if __name__ == "__main__":
    main()
