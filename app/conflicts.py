from app.models import Conflict, PaperCard


def classify(cards: list[PaperCard]) -> Conflict:
    supporting_ids = []
    opposing_ids = []
    mixed_ids = []

    for pc in cards:
        if not pc.card.has_finding or not pc.quote_verified:
            continue

        if pc.card.direction == "supports":
            supporting_ids.append(pc.arxiv_id)

        elif pc.card.direction == "contradicts":
            opposing_ids.append(pc.arxiv_id)

        elif pc.card.direction == "mixed":
            mixed_ids.append(pc.arxiv_id)

    decisive_count = len(supporting_ids) + len(opposing_ids)
    if decisive_count < 2:
        status = "insufficient"

    elif supporting_ids and opposing_ids:
        status = "conflict"

    else:
        status = "agreement"

    return Conflict(
        status=status,
        supporting_ids=supporting_ids,
        opposing_ids=opposing_ids,
        mixed_ids=mixed_ids,
    )
