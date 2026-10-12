import fitz
import os
import sys


# =========================================================
# YOJANAMITRA
# Government Scheme PDF Text Extractor
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_DIR = os.path.join(BASE_DIR, "pdfs")
OUTPUT_DIR = os.path.join(BASE_DIR, "extracted")


def extract_pdf_text(pdf_path):
    """
    Extract readable text from a PDF using PyMuPDF.
    """

    document = fitz.open(pdf_path)

    all_text = []

    for page_number, page in enumerate(document, start=1):

        text = page.get_text("text")

        if text.strip():

            all_text.append(
                f"\n\n===== PAGE {page_number} =====\n\n"
            )

            all_text.append(text)

    document.close()

    return "".join(all_text)


def process_pdf(pdf_filename):

    pdf_path = os.path.join(PDF_DIR, pdf_filename)

    if not os.path.exists(pdf_path):

        print("\nERROR: PDF not found:")
        print(pdf_path)

        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n==========================================")
    print("        YOJANAMITRA PDF EXTRACTOR")
    print("==========================================")

    print(f"\nPDF: {pdf_filename}")
    print("Extracting text...\n")

    try:

        text = extract_pdf_text(pdf_path)

        if not text.strip():

            print("WARNING: No readable text was found.")
            print("This may be a scanned/image-only PDF.")

            return

        output_filename = (
            os.path.splitext(pdf_filename)[0] + ".txt"
        )

        output_path = os.path.join(
            OUTPUT_DIR,
            output_filename
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(text)

        print("SUCCESS!")

        print("\nExtracted text saved to:")
        print(output_path)

        print(f"\nCharacters extracted: {len(text):,}")

    except Exception as error:

        print("\nERROR while processing PDF:")
        print(error)


# =========================================================
# COMMAND LINE
# =========================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print("\nUsage:")
        print("python pdf_extractor.py <pdf_filename>")

        print("\nExample:")
        print(
            "python pdf_extractor.py pm_vishwakarma.pdf"
        )

    else:

        process_pdf(sys.argv[1])