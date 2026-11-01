from app.pdf import fetch_paper_text

text = fetch_paper_text("1706.03762")
print(len(text), "characters")
print(text[:500])
