import pdfplumber
import io
import openpyxl
from docx import Document

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

def read_docx_text(file_bytes):
    """Extract all text and table contents from a DOCX file, joined with newlines."""
    doc = Document(io.BytesIO(file_bytes))
    text_parts = []
    
    
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text.strip())
            
    for table in doc.tables:
        for row in table.rows:
            # Gather non-empty cell values
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                # Deduplicate consecutive identical cells caused by merged cells
                clean_cells = []
                for cell in cells:
                    if not clean_cells or cell != clean_cells[-1]:
                        clean_cells.append(cell)
                
                # Format similarly to your XLSX key-value logic if exactly two items exist
                if len(clean_cells) == 2:
                    text_parts.append(": ".join(clean_cells))
                else:
                    text_parts.append(" ".join(clean_cells))
                    
    return "\n".join(text_parts)