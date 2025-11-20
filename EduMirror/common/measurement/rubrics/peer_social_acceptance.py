from typing import Optional, List

from common.measurement.rater import Rubric, RubricItem


def get_peer_social_acceptance_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []

    items.append(RubricItem(
        id="psa_rejected",
        label="Peer Social Acceptance: Rejected",
        criteria={
            "keywords": [
                "exclude", "go away", "not welcome", "seat is taken", "ignore",
                "laugh at", "tease", "mock", "leave us", "do not join",
            ]
        },
        options=["Rejected", "Neglected", "Accepted"],
        scoring={
            "score_map": {"Rejected": 1.0, "Neglected": 0.5, "Accepted": 0.0},
            "severity_map": {"Rejected": 3, "Neglected": 2, "Accepted": 1},
        },
    ))

    items.append(RubricItem(
        id="psa_neglected",
        label="Peer Social Acceptance: Neglected",
        criteria={
            "keywords": [
                "maybe later", "busy now", "sit anywhere", "we are talking", "not now",
                "polite but", "no invitation", "looks away", "minimal conversation",
            ]
        },
        options=["Neglected", "Rejected", "Accepted"],
        scoring={
            "score_map": {"Accepted": 1.0, "Neglected": 0.5, "Rejected": 0.0},
            "severity_map": {"Accepted": 1, "Neglected": 2, "Rejected": 3},
        },
    ))

    items.append(RubricItem(
        id="psa_accepted",
        label="Peer Social Acceptance: Accepted",
        criteria={
            "keywords": [
                "join us", "sit with us", "welcome", "come over", "invite",
                "share with", "support", "glad you are here", "be with us",
            ]
        },
        options=["Accepted", "Neglected", "Rejected"],
        scoring={
            "score_map": {"Accepted": 1.0, "Neglected": 0.5, "Rejected": 0.0},
            "severity_map": {"Accepted": 1, "Neglected": 2, "Rejected": 3},
        },
    ))

    rubric = Rubric(
        name="Peer Social Acceptance",
        description="Assess peers' acceptance behaviors towards the target student.",
        target_agent=target_agent,
        items=items,
        prompt_template="Rate peer acceptance behaviors based on observed utterances.",
    )
    return rubric

