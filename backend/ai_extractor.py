import json
import os
import re
import sys
import requests
import time


# =========================================================
# YOJANAMITRA
# AI GOVERNMENT SCHEME ELIGIBILITY EXTRACTOR
# Chunked Qwen3 version
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EXTRACTED_DIR = os.path.join(BASE_DIR, "extracted")
AI_OUTPUT_DIR = os.path.join(BASE_DIR, "data", "ai_extracted")

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen3:1.7b"

# Keep chunks reasonably small for an 8 GB RAM laptop.
CHUNK_SIZE = 12000

# Small overlap helps avoid losing information at chunk boundaries.
CHUNK_OVERLAP = 1000


# =========================================================
# LOAD TEXT
# =========================================================

def load_text(filename):

    file_path = os.path.join(
        EXTRACTED_DIR,
        filename
    )

    if not os.path.exists(file_path):

        print("\nERROR: Extracted text file not found:")
        print(file_path)

        return None

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


# =========================================================
# SPLIT DOCUMENT INTO CHUNKS
# =========================================================

def split_into_chunks(text):

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + CHUNK_SIZE,
            text_length
        )

        chunk = text[start:end]

        chunks.append(chunk)

        if end >= text_length:
            break

        start = end - CHUNK_OVERLAP

    return chunks


# =========================================================
# QWEN REQUEST
# =========================================================

def ask_qwen(chunk, chunk_number, total_chunks):

    prompt = f"""
You are an expert analyst extracting eligibility rules from an
Indian government scheme document for a software system.

This is document chunk {chunk_number} of {total_chunks}.

Extract ONLY useful information related to:

- who is eligible
- age requirements
- occupation
- gender
- income limits
- category requirements
- residence requirements
- land requirements
- exclusions
- required documents
- important conditions
- benefits

Do NOT invent information.

If the chunk does not contain relevant information, return empty
lists and null values.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "eligibility": {{
    "min_age": null,
    "max_age": null,
    "gender": "Any",
    "occupation": [],
    "categories": [],
    "max_annual_income": null,
    "land_owned": null,
    "max_land_area_acres": null,
    "residence": [],
    "disability_required": null,
    "excluded_if": {{}}
  }},
  "required_documents": [],
  "important_conditions": [],
  "benefits": [],
  "source_notes": []
}}

Important:
- Do not guess.
- Do not create information that is not present.
- Preserve important conditions even if they do not fit the fields.
- Use empty arrays when nothing relevant is found.
- Return JSON only.
- Do not use Markdown.

DOCUMENT CHUNK:

{chunk}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=600
    )

    response.raise_for_status()

    result = response.json()

    return result.get("response", "")


# =========================================================
# EXTRACT JSON FROM QWEN RESPONSE
# =========================================================

def extract_json(response):

    response = response.strip()

    # Remove markdown fences if Qwen adds them.
    response = response.replace(
        "```json",
        ""
    ).replace(
        "```",
        ""
    ).strip()

    # First attempt: complete response is JSON.
    try:

        return json.loads(response)

    except json.JSONDecodeError:
        pass

    # Second attempt: find the first JSON object.
    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1 and end > start:

        candidate = response[start:end + 1]

        try:

            return json.loads(candidate)

        except json.JSONDecodeError:

            pass

    return None


# =========================================================
# MERGE RESULTS
# =========================================================

def merge_results(results):

    merged = {
        "scheme_name": "PM Vishwakarma",
        "description": "",
        "eligibility": {
            "min_age": None,
            "max_age": None,
            "gender": "Any",
            "occupation": [],
            "categories": [],
            "max_annual_income": None,
            "land_owned": None,
            "max_land_area_acres": None,
            "residence": [],
            "disability_required": None,
            "excluded_if": {}
        },
        "required_documents": [],
        "important_conditions": [],
        "benefits": [],
        "source_notes": []
    }

    for result in results:

        if not isinstance(result, dict):
            continue

        eligibility = result.get(
            "eligibility",
            {}
        )

        if not isinstance(eligibility, dict):
            eligibility = {}

        # -------------------------------------------------
        # Scalar values
        # -------------------------------------------------

        scalar_fields = [
            "min_age",
            "max_age",
            "max_annual_income",
            "max_land_area_acres"
        ]

        for field in scalar_fields:

            value = eligibility.get(field)

            if value is not None:

                if merged["eligibility"][field] is None:
                    merged["eligibility"][field] = value

        # -------------------------------------------------
        # Gender
        # -------------------------------------------------

        gender = eligibility.get("gender")

        if gender and gender != "Any":

            merged["eligibility"]["gender"] = gender

        # -------------------------------------------------
        # Boolean fields
        # -------------------------------------------------

        for field in [
            "land_owned",
            "disability_required"
        ]:

            value = eligibility.get(field)

            if value is not None:

                merged["eligibility"][field] = value

        # -------------------------------------------------
        # List fields
        # -------------------------------------------------

        for field in [
            "occupation",
            "categories",
            "residence"
        ]:

            values = eligibility.get(field, [])

            if isinstance(values, list):

                for value in values:

                    if value and value not in merged[
                        "eligibility"
                    ][field]:

                        merged["eligibility"][field].append(
                            value
                        )

        # -------------------------------------------------
        # Exclusions
        # -------------------------------------------------

        exclusions = eligibility.get(
            "excluded_if",
            {}
        )

        if isinstance(exclusions, dict):

            for key, value in exclusions.items():

                if key not in merged[
                    "eligibility"
                ]["excluded_if"]:

                    merged[
                        "eligibility"
                    ]["excluded_if"][key] = value

        # -------------------------------------------------
        # Other lists
        # -------------------------------------------------

        for field in [
            "required_documents",
            "important_conditions",
            "benefits",
            "source_notes"
        ]:

            values = result.get(
                field,
                []
            )

            if isinstance(values, list):

                for value in values:

                    if value and value not in merged[field]:

                        merged[field].append(
                            value
                        )

    return merged


# =========================================================
# MAIN PROCESS
# =========================================================

def process_document(filename):

    print("\n==========================================")
    print("       YOJANAMITRA AI EXTRACTOR")
    print("==========================================")

    print(f"\nInput file: {filename}")
    print(f"AI model: {MODEL_NAME}")

    document_text = load_text(filename)

    if not document_text:

        return

    print(
        f"\nDocument characters: {len(document_text):,}"
    )

    chunks = split_into_chunks(
        document_text
    )

    print(
        f"Document split into {len(chunks)} chunks."
    )

    print(
        f"Chunk size: approximately {CHUNK_SIZE:,} characters."
    )

    successful_results = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        print(
            f"\n------------------------------------------"
        )

        print(
            f"Processing chunk {index}/{len(chunks)}..."
        )

        try:

            raw_response = ask_qwen(
                chunk,
                index,
                len(chunks)
            )

            structured_result = extract_json(
                raw_response
            )

            if structured_result is None:

                print(
                    f"WARNING: Chunk {index} returned invalid JSON."
                )

                print(
                    "Skipping this chunk."
                )

                continue

            successful_results.append(
                structured_result
            )

            print(
                f"Chunk {index} processed successfully."
            )

        except requests.exceptions.ConnectionError:

            print(
                "\nERROR: Cannot connect to Ollama."
            )

            print(
                "Make sure Ollama is running."
            )

            return

        except requests.exceptions.Timeout:

            print(
                f"\nWARNING: Chunk {index} timed out."
            )

        except Exception as error:

            print(
                f"\nWARNING: Chunk {index} failed:"
            )

            print(error)

        # Give the system a tiny breathing period.
        time.sleep(1)

    # -----------------------------------------------------
    # CHECK RESULTS
    # -----------------------------------------------------

    if not successful_results:

        print(
            "\nERROR: No chunks were successfully processed."
        )

        return

    print(
        "\n=========================================="
    )

    print(
        "Combining AI extraction results..."
    )

    final_result = merge_results(
        successful_results
    )

    # -----------------------------------------------------
    # SAVE RESULT
    # -----------------------------------------------------

    os.makedirs(
        AI_OUTPUT_DIR,
        exist_ok=True
    )

    output_filename = (
        os.path.splitext(filename)[0]
        + "_eligibility.json"
    )

    output_path = os.path.join(
        AI_OUTPUT_DIR,
        output_filename
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_result,
            file,
            indent=2,
            ensure_ascii=False
        )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    print(
        "\n=========================================="
    )

    print(
        "SUCCESS!"
    )

    print(
        "=========================================="
    )

    print(
        f"\nSuccessful chunks: "
        f"{len(successful_results)}/{len(chunks)}"
    )

    print(
        "\nStructured eligibility saved to:"
    )

    print(
        output_path
    )

    print(
        "\nFinal extracted structure:"
    )

    print(
        json.dumps(
            final_result,
            indent=2,
            ensure_ascii=False
        )
    )


# =========================================================
# COMMAND LINE
# =========================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print("\nUsage:")

        print(
            "python ai_extractor.py <extracted_text_file>"
        )

        print("\nExample:")

        print(
            "python ai_extractor.py pm_vishwakarma.txt"
        )

    else:

        process_document(
            sys.argv[1]
        )