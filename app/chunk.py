import re
from app.models import Chunk

HEADING = re.compile(r"^\d+(\.\d+)*\s+[A-Z][A-Za-z ,\-]{2,60}$")
NUM_ONLY = re.compile(r"^\d+(\.\d+)*$")
TITLE_ONLY = re.compile(r"^[A-Z][A-Za-z ,\-]{2,60}$")


def _top_level(section: str) -> int:
    first = section.split()[0]
    return int(first.split(".")[0]) if first[0].isdigit() else 0


def split_sections(text: str) -> list[tuple[str, str]]:
    idx = text.rfind("References")
    if idx > 0:
        text = text[:idx]

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    sections = []
    current_section = "Unknown"
    current_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        heading = None

        if HEADING.match(line):
            heading = line
        elif (
            NUM_ONLY.match(line)
            and i + 1 < len(lines)
            and TITLE_ONLY.match(lines[i + 1])
        ):
            heading = f"{line} {lines[i + 1]}"
            i += 1

        # new: reject a top-level heading whose number doesn't go up
        if heading and "." not in heading.split()[0]:
            if int(heading.split()[0]) <= _top_level(current_section):
                heading = None
                if NUM_ONLY.match(line):
                    i -= 1

        if heading:
            if current_lines:
                sections.append((current_section, " ".join(current_lines)))
            current_section = heading
            current_lines = []
        else:
            current_lines.append(line)

        i += 1

    if current_lines:
        sections.append((current_section, " ".join(current_lines)))

    return sections


def make_chunks(
    arxiv_id: str,
    sections: list[tuple[str, str]],
    size: int = 200,
    overlap: int = 50,
) -> list[Chunk]:
    chunks = []
    step = size - overlap

    for name, body in sections:
        words = body.split()
        if len(words) < 20:
            continue

        for start in range(0, len(words), step):
            piece = words[start : start + size]
            chunks.append(Chunk(arxiv_id=arxiv_id, section=name, text=" ".join(piece)))
            if start + size >= len(words):
                break

    return chunks
