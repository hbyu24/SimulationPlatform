from typing import Optional, List

from common.measurement.rater import Rubric, RubricItem


def get_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []
    items.append(
        RubricItem(
            id="equality",
            label="Equal Status",
            criteria={"keywords": [
                "equal", "treated as equal", "same level", "respect as equal"
            ]},
            options=["Present"],
            scoring={"score_map": {"Present": 1}, "severity_map": {"Present": 1}},
        )
    )
    items.append(
        RubricItem(
            id="cooperation",
            label="Cooperation",
            criteria={"keywords": [
                "cooperate", "work together", "team up", "solve together"
            ]},
            options=["Present"],
            scoring={"score_map": {"Present": 1}, "severity_map": {"Present": 1}},
        )
    )
    items.append(
        RubricItem(
            id="affect",
            label="Affect/Enjoyment",
            criteria={"keywords": [
                "pleasant", "enjoy", "positive", "good atmosphere", "friendly"
            ]},
            options=["Present"],
            scoring={"score_map": {"Present": 1}, "severity_map": {"Present": 1}},
        )
    )
    return Rubric(
        name="intergroup_contact_quality",
        description="Intergroup Contact Quality Rubric",
        target_agent=target_agent,
        items=items,
        prompt_template="Detect intergroup contact quality markers",
    )

