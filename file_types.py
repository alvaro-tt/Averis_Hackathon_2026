IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")


def get_file_type(path):
    p = str(path).lower()
    if p.endswith(".txt"):
        return "txt"
    elif p.endswith(".pdf"):
        return "pdf"
    elif p.endswith(".docx"):
        return "docx"
    elif p.endswith(".xlsx"):
        return "xlsx"
    elif p.endswith(IMAGE_EXTENSIONS):
        return "image"       # scanned page -> OCR
    else:
        return "unknown"