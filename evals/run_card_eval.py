import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.cards import make_cards
from app.models import Chunk, Paper, SourcePlatform


def main() -> None:
    dataset = json.loads((ROOT / "evals/card_eval.json").read_text())
    items = dataset["items"]

    papers = [
        Paper(
            title=item["title"],
            abstract=item["abstract"],
            authors=[],
            url=f"https://arxiv.org/abs/{item['arxiv_id']}",
            source=SourcePlatform.ARXIV,
            arxiv_id=item["arxiv_id"],
        )
        for item in items
    ]
    evidence = [
        Chunk(arxiv_id=item["arxiv_id"], section=passage["section"], text=passage["text"])
        for item in items
        for passage in item["passages"]
    ]

    cards = make_cards(dataset["question"], papers, evidence)
    expected_has_finding = [item["expected_has_finding"] for item in items]
    expected_answers = [item["expected_answer"] for item in items]
    has_finding_correct = sum(
        card.card.has_finding == expected
        for card, expected in zip(cards, expected_has_finding)
    )
    answer_correct = sum(
        card.card.answer == expected
        for card, expected in zip(cards, expected_answers)
    )
    exact_correct = sum(
        card.card.has_finding == item["expected_has_finding"]
        and card.card.answer == item["expected_answer"]
        for card, item in zip(cards, items)
    )
    finding_answer_correct = sum(
        card.card.answer == item["expected_answer"]
        for card, item in zip(cards, items)
        if item["expected_has_finding"]
    )
    finding_count = sum(expected_has_finding)

    report = {
        "question": dataset["question"],
        "item_count": len(items),
        "metrics": {
            "has_finding_accuracy": has_finding_correct / len(items),
            "answer_accuracy_all": answer_correct / len(items),
            "answer_accuracy_on_findings": finding_answer_correct / finding_count,
            "exact_accuracy": exact_correct / len(items),
        },
        "items": [
            {
                "arxiv_id": item["arxiv_id"],
                "title": item["title"],
                "expected_has_finding": item["expected_has_finding"],
                "expected_answer": item["expected_answer"],
                "actual_has_finding": card.card.has_finding,
                "actual_answer": card.card.answer,
                "quote_verified": card.quote_verified,
                "finding": card.card.finding,
                "label_note": item["label_note"],
                "correct": (
                    card.card.has_finding == item["expected_has_finding"]
                    and card.card.answer == item["expected_answer"]
                ),
            }
            for item, card in zip(items, cards)
        ],
    }
    report_path = ROOT / "cache/card_eval_results.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(f"Papers: {len(items)}")
    print(f"has_finding accuracy: {has_finding_correct}/{len(items)} ({has_finding_correct / len(items):.0%})")
    print(f"answer accuracy (all): {answer_correct}/{len(items)} ({answer_correct / len(items):.0%})")
    print(f"answer accuracy (papers with findings): {finding_answer_correct}/{finding_count} ({finding_answer_correct / finding_count:.0%})")
    print(f"exact finding + answer match: {exact_correct}/{len(items)} ({exact_correct / len(items):.0%})")
    print(f"Saved report: {report_path}")
    print("\nPer-paper results:")
    for item, card in zip(items, cards):
        print(
            f"{item['arxiv_id']}: finding {card.card.has_finding} "
            f"(gold {item['expected_has_finding']}), answer {card.card.answer} "
            f"(gold {item['expected_answer']}), quote_verified {card.quote_verified}"
        )
        print(f"  finding: {card.card.finding}")
        print(f"  label note: {item['label_note']}")


if __name__ == "__main__":
    main()
