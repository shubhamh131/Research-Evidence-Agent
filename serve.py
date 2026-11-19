import json
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent

app = Flask(__name__)

# Limit incoming request size
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024


@app.route("/", methods=["GET"])
def home():
    return send_from_directory(ROOT, "index.html")


@app.route("/api/evals/latest", methods=["GET"])
def latest_eval():
    report_path = ROOT / "cache" / "card_eval_results.json"

    if not report_path.exists():
        return jsonify({"error": "No card evaluation report yet."}), 404

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
        return jsonify(data)
    except (json.JSONDecodeError, OSError):
        app.logger.exception("Could not read evaluation report")
        return jsonify({"error": "Could not read evaluation report."}), 500


@app.route("/api/research", methods=["POST"])
def research():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON request."}), 400

    question = str(payload.get("question", "")).strip()

    if not question:
        return jsonify({"error": "Enter a research question first."}), 400

    if len(question) > 1000:
        return jsonify({"error": "Questions must be 1,000 characters or fewer."}), 400

    try:
        from app.chain import run

        result, timings = run(question)

        cards_by_id = {card.arxiv_id: card for card in result["cards"]}

        evidence_by_id = {}

        for chunk in result["evidence"]:
            evidence_by_id.setdefault(chunk.arxiv_id, []).append(
                {
                    "section": chunk.section,
                    "text": chunk.text,
                }
            )

        papers = []

        for screened in result["top"]:
            paper = screened.paper
            paper_card = cards_by_id.get(paper.arxiv_id)

            if paper_card is None:
                continue

            papers.append(
                {
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "url": str(paper.url),
                    "year": paper.year,
                    "authors": paper.authors,
                    "relevance": screened.relevance,
                    "screen_direction": screened.direction,
                    "screen_reason": screened.reason,
                    "quote_verified": paper_card.quote_verified,
                    "card": paper_card.card.model_dump(mode="json"),
                    "evidence": evidence_by_id.get(paper.arxiv_id, []),
                }
            )

        return jsonify(
            {
                "question": question,
                "plan": result["plan"].model_dump(mode="json"),
                "papers": papers,
                "conflict": result["conflict"].model_dump(mode="json"),
                "timings": timings,
                "total_seconds": sum(timings.values()),
            }
        )

    except Exception:
        app.logger.exception("Research run failed")
        return jsonify({"error": "Research run failed. Please try again."}), 500


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8000))

    print(f"Research Evidence Agent running on {host}:{port}")

    app.run(host=host, port=port, debug=False)
