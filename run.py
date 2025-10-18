import google.generativeai as genai
import os
from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# ==========================
# --- GEMINI CONFIG ---
# ==========================
genai.configure(api_key="AIzaSyADlBTWfleg_PLTvOZ23l-6mVu4mmHNrNE")
model = genai.GenerativeModel("gemini-2.5-flash")

# ==========================
# --- FILE PATHS ---
# ==========================
PDF_FILE_PATH = "bio.pdf"
PDF_FILE_OPTIONAL1 = "added1.pdf"
PDF_FILE_OPTIONAL2 = "added2.pdf"

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_EXAM_PATH = f"output/Mock_Exam_Generated_{TIMESTAMP}.pdf"
OUTPUT_ANSW_PATH = f"output/Mock_Answers_Generated_{TIMESTAMP}.pdf"

# ==========================
# --- PDF EXTRACTION ---
# ==========================
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a given PDF using PyMuPDF (fitz)."""
    try:
        import fitz
        if not Path(pdf_path).exists():
            return f"ERROR: File not found at path: {pdf_path}"
        with fitz.open(pdf_path) as doc:
            text = "".join(page.get_text() for page in doc)
        return text
    except Exception as e:
        return f"ERROR: {e}"

# ==========================
# --- EXAM GENERATION ---
# ==========================
def generate_mock_exam(pdf_text: str):
    """Generates a balanced mock exam from multiple subjects using Gemini."""
    numMC = os.environ.get("num_MC_questions")
    numFTB = os.environ.get("num_FTB_questions")
    numTF = os.environ.get("num_TF_questions")
    lang = os.environ.get("language", "English")

    try:
        numquestions = int(numMC) + int(numFTB) + int(numTF)
    except Exception:
        return "ERROR: Invalid or missing environment variables for question counts."

    prompt = f"""
    You are generating a mixed-topic exam. The text below comes from several different subjects.
    Make sure the exam includes questions from ALL subjects represented in the text,
    not just the first one.

    Generate {numquestions} total questions:
    - {numMC} multiple choice
    - {numFTB} fill in the blank
    - {numTF} true/false

    Each question must include:
    - Four labeled answers (A-D) or True/False options
    - A clearly marked correct answer line: "ANSWER: [Letter/True/False]"
    Do NOT include any section headers like "Mock Exam:", "Instructions:", or "---".
    The exam should be written in {lang}.

    --- TEXT START ---
    {pdf_text}
    --- TEXT END ---
    """

    try:
        response = model.generate_content(prompt)
        exam_text = response.text

        # --- Post-process cleanup: remove unwanted headers ---
        cleaned_lines = []
        skip_phrases = ["mock exam", "instructions", "multiple choice", "---"]
        for line in exam_text.splitlines():
            lower = line.lower().strip()
            if any(phrase in lower for phrase in skip_phrases):
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines).strip()

    except Exception as e:
        return f"ERROR: Gemini API call failed: {e}"


# ==========================
# --- PDF EXPORT (ReportLab) ---
# ==========================
def export_exam_to_pdf(exam_text: str, output_path: str):
    """Exports the given exam text into a formatted PDF."""
    styles = getSampleStyleSheet()
    story = []

    # --- Custom styles ---
    # (use unique names to avoid collision with default ones)
    styles.add(ParagraphStyle(name="QuestionStyle", fontName="Times-Bold", fontSize=11, spaceAfter=6, leading=14))
    styles.add(ParagraphStyle(name="AnswerStyle", fontName="Times-Roman", fontSize=10, leftIndent=20, spaceAfter=3))
    styles.add(ParagraphStyle(name="CorrectStyle", fontName="Times-Bold", fontSize=10, textColor=colors.red, spaceBefore=5, spaceAfter=10))

    # Modify existing "Title" style safely
    styles["Title"].fontName = "Times-Bold"
    styles["Title"].fontSize = 18
    styles["Title"].alignment = 1
    styles["Title"].spaceAfter = 20

    # --- Title ---
    title = os.environ.get("exam_title", "GENERATED MOCK EXAM")
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    # --- Process lines ---
    for line in exam_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.upper().startswith("ANSWER:"):
            story.append(Paragraph(line, styles["CorrectStyle"]))
            story.append(Spacer(1, 8))
        elif line[0].isdigit() and line.find('.') < 3:
            story.append(Paragraph(line, styles["QuestionStyle"]))
        elif line.startswith(("A)", "B)", "C)", "D)")) or line.startswith(("A.", "B.", "C.", "D.")):
            story.append(Paragraph(line, styles["AnswerStyle"]))
        else:
            story.append(Paragraph(line, styles["AnswerStyle"]))

    # --- Create PDF ---
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        canvas.setFont("Times-Roman", 9)
        canvas.drawRightString(200 * mm, 15 * mm, str(page_num))

    try:
        doc.build(story, onLaterPages=add_page_number, onFirstPage=add_page_number)
        print(f"✅ Exported PDF: {output_path}")
        return True
    except Exception as e:
        return f"ERROR: Could not save PDF: {e}"

# ==========================
# --- SPLIT EXAM ---
# ==========================
def split_exam_text(exam_text: str):
    """Splits the full exam text into question-only and answer-only parts."""
    questions, answers = [], []
    for line in exam_text.splitlines():
        if line.strip().upper().startswith("ANSWER:"):
            answers.append(line.strip())
        else:
            questions.append(line.strip())
    return "\n".join(questions), "\n".join(answers)

def export_exam_and_answers(exam_text: str, questions_pdf: str, answers_pdf: str):
    """Exports separate PDFs for questions and answers."""
    q_text, a_text = split_exam_text(exam_text)
    q_result = export_exam_to_pdf(q_text, questions_pdf)
    a_result = export_exam_to_pdf(a_text, answers_pdf)
    return q_result, a_result

# ==========================
# --- MAIN ---
# ==========================
if __name__ == "__main__":
    print(f"Reading: {PDF_FILE_PATH}")
    combined_content = ""

    main_text = extract_text_from_pdf(PDF_FILE_PATH)
    if main_text.startswith("ERROR"):
        print(main_text)
        exit(1)
    combined_content += main_text

    # Optional PDFs
    for extra_path in [PDF_FILE_OPTIONAL1, PDF_FILE_OPTIONAL2]:
        if Path(extra_path).exists():
            combined_content += "\n\n" + extract_text_from_pdf(extra_path)

    print("Generating exam...")
    exam = generate_mock_exam(combined_content)

    if exam.startswith("ERROR"):
        print(exam)
    else:
        splitexam = os.environ.get("split_exam")
        if splitexam in [False, "False", "false", None]:
            export_exam_to_pdf(exam, OUTPUT_EXAM_PATH)
        else:
            export_exam_and_answers(exam, OUTPUT_EXAM_PATH, OUTPUT_ANSW_PATH)
