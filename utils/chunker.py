def chunk_text(text: str, max_chars: int = 120000):
    chunks = []
    current = ""

    for paragraph in text.split("\n"):
        if len(current) + len(paragraph) < max_chars:
            current += paragraph + "\n"
        else:
            chunks.append(current.strip())
            current = paragraph + "\n"

    if current.strip():
        chunks.append(current.strip())


    return chunks
