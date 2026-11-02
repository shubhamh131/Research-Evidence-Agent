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

        if heading:
            parts = heading.split()[0].split(".")
            top = int(parts[0])
            cur = _top_level(current_section)
            if len(parts) == 1:
                bad = top != cur + 1
            else:
                bad = top not in (cur, cur + 1) or int(parts[1]) == 0
            if bad:
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
            numeric = sum(any(ch.isdigit() for ch in w) for w in piece)
            if numeric / len(piece) < 0.3 and "@" not in " ".join(piece):
                chunks.append(
                    Chunk(arxiv_id=arxiv_id, section=name, text=" ".join(piece))
                )
            if start + size >= len(words):
                break

    return chunks
