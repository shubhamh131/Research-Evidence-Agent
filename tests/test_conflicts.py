import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models import PaperCard, StudyCard
from app.conflicts import classify


def make_card(arxiv_id, answer, verified=True, has_finding=True):
    card = StudyCard(
        method="Dummy research method",
        setting="Dummy research setting",
        finding="Dummy research finding",
        implication="Dummy implication",
        answer=answer,
        quote="Dummy verified quote",
        limitations="Dummy limitations",
        has_finding=has_finding,
    )

    return PaperCard(
        arxiv_id=arxiv_id,
        title=f"Dummy paper {arxiv_id}",
        card=card,
        quote_verified=verified,
    )


def test_conflict():
    cards = [
        make_card("paper1", "yes"),
        make_card("paper2", "no"),
        make_card("paper3", "no"),
    ]

    result = classify(cards)

    assert result.status == "conflict"
    assert result.supporting_ids == ["paper1"]
    assert result.opposing_ids == ["paper2", "paper3"]
    assert result.mixed_ids == []


def test_agreement():
    cards = [
        make_card("paper1", "yes"),
        make_card("paper2", "yes"),
        make_card("paper3", "yes"),
    ]

    result = classify(cards)

    assert result.status == "agreement"
    assert result.supporting_ids == ["paper1", "paper2", "paper3"]
    assert result.opposing_ids == []
    assert result.mixed_ids == []


def test_insufficient():
    cards = [make_card("paper1", "yes")]

    result = classify(cards)

    assert result.status == "insufficient"
    assert result.supporting_ids == ["paper1"]
    assert result.opposing_ids == []
    assert result.mixed_ids == []


def test_unverified_card_is_ignored():
    cards = [
        make_card("paper1", "yes"),
        make_card("paper2", "yes"),
        make_card("paper3", "no", verified=False),
    ]

    result = classify(cards)

    assert result.status == "agreement"
    assert result.supporting_ids == ["paper1", "paper2"]
    assert result.opposing_ids == []
    assert result.mixed_ids == []


def test_unclear_card_does_not_count_as_agreement():
    cards = [
        make_card("paper1", "yes"),
        make_card("paper2", "unclear"),
    ]

    result = classify(cards)

    assert result.status == "insufficient"
    assert result.supporting_ids == ["paper1"]
    assert result.opposing_ids == []
    assert result.mixed_ids == []
