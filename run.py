import google.generativeai as genai
import os
import fitz # PyMuPDF
from pathlib import Path
from datetime import datetime

genai.configure(api_key="AIzaSyADlBTWfleg_PLTvOZ23l-6mVu4mmHNrNE")

model = genai.GenerativeModel("gemini-2.5-flash")

PDF_FILE_PATH = "bio.pdf"

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_EXAM_PATH = f"output\\Mock_Exam_Generated_{TIMESTAMP}.pdf"
OUTPUT_ANSW_PATH = f"output\\Mock_Answers_Generated_{TIMESTAMP}.pdf"

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text content from a PDF file using PyMuPDF (fitz).
    """
    try:
        if not Path(pdf_path).exists():
            return f"ERROR: File not found at path: {pdf_path}"

        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"ERROR: An error occurred during PDF processing: {e}"

def generate_mock_exam(pdf_text: str):
    """
    Uses the extracted PDF text to generate a multiple-choice mock exam.
    """
    prompt = f"""
    Based ONLY on the following text content, generate a mock exam consisting of 5 challenging multiple-choice questions.

    Each question MUST have:
    1. The Question text.
    2. Exactly 4 possible answers, labeled A, B, C, and D.
    3. The correct answer clearly indicated on a separate line as 'ANSWER: [Letter]'.

    Do not include any introductory or concluding text, just the questions and answers.
    Ensure all questions and options are on separate lines for easy parsing.

    --- TEXT CONTENT START ---
    {pdf_text}
    --- TEXT CONTENT END ---
    """

    print("Generating exam with Gemini... (This may take a moment)")

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ERROR: Gemini API call failed: {e}"

def export_exam_to_pdf(exam_text: str, output_path: str):
    """
    Creates a readable PDF for a mock exam with proper spacing, wrapping, and page breaks.
    """
    import fitz

    doc = fitz.open()
    width, height = fitz.paper_rect("A4")[2:4]
    margin = 50
    line_spacing = 4  # space between lines

    # --- First page ---
    page = doc.new_page()

    # --- Title ---
    title_rect = fitz.Rect(margin, margin, width - margin, margin + 40)
    page.insert_textbox(
        title_rect,
        "GENERATED MOCK EXAM",
        fontname="Times-Bold",
        fontsize=18,
        align=fitz.TEXT_ALIGN_CENTER
    )

    y_cursor = margin + 50  # start below title

    # --- Write content line by line ---
    for line in exam_text.split('\n'):
        line = line.strip()
        if not line:
            y_cursor += line_spacing 
            continue

        fontname = "Times-Roman"
        fontsize = 10
        color = (0, 0, 0)

        if line.upper().startswith("ANSWER:"):
            fontname = "Times-Bold"
            color = (1, 0, 0)
        elif line[0].isdigit() and line.find('.') < 3:
            fontname = "Times-Bold"
            fontsize = 11

        # --- rectangle for wrapping text ---
        max_height = height - margin - y_cursor
        text_rect = fitz.Rect(margin, y_cursor, width - margin, y_cursor + 70)

        used_height = page.insert_textbox(
            text_rect,
            line,
            fontname=fontname,
            fontsize=fontsize,
            color=color,
            align=fitz.TEXT_ALIGN_CENTER,
            expandtabs=True
        )
        y_cursor += used_height + line_spacing

        if y_cursor > height - margin:
            page = doc.new_page()
            y_cursor = margin

    try:
        doc.save(output_path)
        doc.close()
        return True
    except Exception as e:
        return f"ERROR: Could not save PDF file: {e}"

def split_exam_text(exam_text: str):
    """
    Splits the text into questions and answers.
    """
    questions, answers = [], []
    for line in exam_text.splitlines():
        if line.strip().upper().startswith("ANSWER:"):
            answers.append(line.strip())
        else:
            questions.append(line.strip())
    return "\n".join(questions), "\n".join(answers)


def export_exam_and_answers(exam_text: str, questions_pdf: str, answers_pdf: str):
    """
    Splits exam text and exports questions and answers to separate PDF files.
    """
    questions_text, answers_text = split_exam_text(exam_text)

    q_result = export_exam_to_pdf(questions_text, questions_pdf)
    a_result = export_exam_to_pdf(answers_text, answers_pdf)

    return q_result, a_result


if __name__ == "__main__":
    print(f"Attempting to read PDF from: {PDF_FILE_PATH}...")
    
    content = extract_text_from_pdf(PDF_FILE_PATH)
    
    if content.startswith("ERROR"):
        print(f"\n{content}")
    else:
        exam = generate_mock_exam(content)

        if exam.startswith("ERROR"):
            print(f"\n{exam}")
        else:
            splitexam = os.environ.get("split_exam")
            print(splitexam)
            if splitexam is False or splitexam == "False":
                export_exam_to_pdf(exam, OUTPUT_EXAM_PATH)
            if splitexam is True or splitexam == "True":
                export_exam_and_answers(exam, OUTPUT_EXAM_PATH, OUTPUT_ANSW_PATH)
