from app.chunk import split_sections, make_chunks
from app.pdf import fetch_paper_text


text = fetch_paper_text("1706.03762")
for name, body in split_sections(text):
    print(f"{len(body.split()):5} words | {name}")

lines = text.split("\n")
for i, line in enumerate(lines):
    if "Introduction" in line:
        print(i, [lines[i - 1], line])


chunks = make_chunks("1706.03762", split_sections(text))
print(len(chunks), "chunks")
print(chunks[3].section)
print(chunks[3].text)
