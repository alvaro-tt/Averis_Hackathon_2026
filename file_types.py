def get_file_type(path):
    if path.lower().endswith(".txt"):
        return "txt"
    elif path.lower().endswith(".pdf"):
        return "pdf"
    elif path.lower().endswith(".docx"):
        return "docx"
    elif path.lower().endswith(".xlsx"):
        return "xlsx"
    else:
        return "unknown"
