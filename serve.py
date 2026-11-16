import json
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8000


class ResearchHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/evals/latest":
            report_path = ROOT / "cache/card_eval_results.json"
            if not report_path.exists():
                self._send_json({"error": "No card evaluation report yet."}, 404)
                return
            self._send_json(json.loads(report_path.read_text()))
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/research":
            self._send_json({"error": "Endpoint not found."}, 404)
            return

        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size))
            question = str(payload.get("question", "")).strip()
            if not question:
                self._send_json({"error": "Enter a research question first."}, 400)
                return
            if len(question) > 1000:
                self._send_json({"error": "Questions must be 1,000 characters or fewer."}, 400)
                return

            from app.chain import run

            result, timings = run(question)
            cards_by_id = {card.arxiv_id: card for card in result["cards"]}
            evidence_by_id = {}
            for chunk in result["evidence"]:
                evidence_by_id.setdefault(chunk.arxiv_id, []).append(
                    {"section": chunk.section, "text": chunk.text}
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

            self._send_json(
                {
                    "question": question,
                    "plan": result["plan"].model_dump(mode="json"),
                    "papers": papers,
                    "conflict": result["conflict"].model_dump(mode="json"),
                    "timings": timings,
                    "total_seconds": sum(timings.values()),
                }
            )
        except Exception as exc:
            self._send_json({"error": f"Research run failed: {exc}"}, 500)


if __name__ == "__main__":
    print(f"Research Evidence Agent available at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the local server.")
    try:
        HTTPServer((HOST, PORT), ResearchHandler).serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
