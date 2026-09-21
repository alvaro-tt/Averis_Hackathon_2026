import pdfplumber
import io
import openpyxl


def read_pdf_text(file_bytes):
    """Extract all text from a PDF, page by page, joined with newlines."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)

def read_xlsx_text(file_bytes):
    """Extract all cell values from an XLSX, formatted as readable lines."""
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    text_parts = []
    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
            if cells:
                text_parts.append(": ".join(cells) if len(cells) == 2 else " ".join(cells))
    return "\n".join(text_parts)