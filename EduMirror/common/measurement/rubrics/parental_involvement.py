from typing import List

from common.measurement.rater import Rubric, RubricItem


def get_parental_involvement_rubric() -> Rubric:
    items: List[RubricItem] = [
        RubricItem(
            id="decision_making",
            label="Decision Making",
            criteria={"keywords": [
                "committee",
                "input",
                "vote",
                "policy",
                "set goals",
                "priorities",
            ]},
            options=["present"],
            scoring={"score_map": {"present": 1}, "severity_map": {"present": 2}},
        ),
        RubricItem(
            id="volunteering",
            label="Volunteering",
            criteria={"keywords": [
                "volunteer",
                "take responsibility",
                "help",
                "offer time",
                "complete tasks",
                "follow through",
            ]},
            options=["present"],
            scoring={"score_map": {"present": 1}, "severity_map": {"present": 2}},
        ),
    ]
    return Rubric(
        name="ParentalInvolvement",
        description="Parental Involvement Rubric (Epstein’s Framework)",
        target_agent=None,
        items=items,
        prompt_template="",
    )

