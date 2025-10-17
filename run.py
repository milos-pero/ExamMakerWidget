import google.generativeai as genai
import os
import fitz # PyMuPDF
from pathlib import Path

# --- Configuration ---
# NOTE: Replace the placeholder with an actual, secure API key.
genai.configure(api_key="AIzaSyADlBTWfleg_PLTvOZ23l-6mVu4mmHNrNE")

model = genai.GenerativeModel("gemini-2.5-flash")

# ==========================================================
# 🚀 NEW: DEFINE THE FILE PATH HERE
# ==========================================================
# IMPORTANT: Update this variable with the exact path to your PDF file.
# You can use a raw string (r"...") for Windows paths to handle backslashes.
PDF_FILE_PATH = "testPDFs\\bio.pdf" 
# Example for Mac/Linux:
# PDF_FILE_PATH = "/Users/YourName/Documents/my_chapter_notes.pdf"
# ==========================================================

# --- PDF Processing Function ---
def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text content from a PDF file using PyMuPDF (fitz).
    """
    try:
        # Use Pathlib to check if the file exists robustly
        if not Path(pdf_path).exists():
            return f"ERROR: File not found at path: {pdf_path}"

        doc = fitz.open(pdf_path)
        text = ""
        # Loop through each page and extract text
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"ERROR: An error occurred during PDF processing: {e}"

# --- Exam Generation Function ---
def generate_mock_exam(pdf_text: str):
    """
    Uses the extracted PDF text to generate a multiple-choice mock exam.
    """
    # Craft a precise prompt to guide the model's output format
    prompt = f"""
    Based ONLY on the following text content, generate a mock exam consisting of 5 challenging multiple-choice questions.

    Each question MUST have:
    1. The Question text.
    2. Exactly 4 possible answers, labeled A, B, C, and D.
    3. The correct answer clearly indicated on a separate line as 'ANSWER: [Letter]'.

    Do not include any introductory or concluding text, just the questions and answers.

    --- TEXT CONTENT START ---
    {pdf_text}
    --- TEXT CONTENT END ---
    """

    print("🧠 Generating exam... (This may take a moment)")

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ERROR: Gemini API call failed: {e}"

# --- Main Execution Block ---
if __name__ == "__main__":
    print(f"📄 Attempting to read PDF from: {PDF_FILE_PATH}...")
    
    # 1. Extract Text
    content = extract_text_from_pdf(PDF_FILE_PATH)
    
    if content.startswith("ERROR"):
        print(f"\n{content}")
    else:
        # 2. Generate Exam
        exam = generate_mock_exam(content)

        # 3. Print Result
        print("\n" + "="*50)
        print("🌟 GENERATED MOCK EXAM 🌟")
        print("="*50)
        print(exam)
        print("="*50 + "\n")