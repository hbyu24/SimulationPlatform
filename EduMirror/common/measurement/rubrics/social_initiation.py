from typing import Optional, List

from common.measurement.rater import Rubric, RubricItem


def get_social_initiation_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []

    items.append(RubricItem(
        id="si_withdrawal",
        label="Social Initiation: Withdrawal",
        criteria={
            "keywords": [
                "looks away", "avoids eye contact", "silent", "stays quiet",
                "waits to be approached", "brief answer", "passive response",
            ]
        },
        options=["Withdrawal", "Hesitant", "Active"],
        scoring={
            "score_map": {"Active": 1.0, "Hesitant": 0.5, "Withdrawal": 0.0},
            "severity_map": {"Active": 1, "Hesitant": 2, "Withdrawal": 3},
        },
    ))

    items.append(RubricItem(
        id="si_hesitant",
        label="Social Initiation: Hesitant",
        criteria={
            "keywords": [
                "tries to start", "starts then stops", "speaks quietly", "hesitant",
                "unsure", "withdraws quickly", "lets others take over",
            ]
        },
        options=["Hesitant", "Withdrawal", "Active"],
        scoring={
            "score_map": {"Active": 1.0, "Hesitant": 0.5, "Withdrawal": 0.0},
            "severity_map": {"Active": 1, "Hesitant": 2, "Withdrawal": 3},
        },
    ))

    items.append(RubricItem(
        id="si_active",
        label="Social Initiation: Active",
        criteria={
            "keywords": [
                "starts conversation", "proactively", "shares personal information", "offers suggestion",
                "makes request", "proposes topic", "initiates",
            ]
        },
        options=["Active", "Hesitant", "Withdrawal"],
        scoring={
            "score_map": {"Active": 1.0, "Hesitant": 0.5, "Withdrawal": 0.0},
            "severity_map": {"Active": 1, "Hesitant": 2, "Withdrawal": 3},
        },
    ))

    rubric = Rubric(
        name="Social Initiation",
        description="Assess the target student's social initiation level.",
        target_agent=target_agent,
        items=items,
        prompt_template="Rate social initiation behaviors based on observed utterances.",
    )
    return rubric

