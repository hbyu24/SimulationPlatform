from typing import Optional, List

from common.measurement.rater import Rubric, RubricItem


def get_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []
    items.append(
        RubricItem(
            id="noticing",
            label="Notice the Event",
            criteria={"keywords": [
                "notice", "see", "aware", "pay attention", "watching"
            ]},
            options=["Present"],
            scoring={"score_map": {"Present": 1}, "severity_map": {"Present": 1}},
        )
    )
    items.append(
        RubricItem(
            id="interpreting",
            label="Interpret as Emergency",
            criteria={"keywords": [
                "serious", "urgent", "needs help", "at risk", "danger"
            ]},
            options=["Present"],
            scoring={"score_map": {"Present": 1}, "severity_map": {"Present": 1}},
        )
    )
    items.append(
        RubricItem(
            id="responsibility",
            label="Assume Responsibility",
            criteria={"keywords": [
                "should help", "i must help", "i will help", "up to me", "my responsibility"
            ]},
            options=["Present"],
            scoring={"score_map": {"Present": 1}, "severity_map": {"Present": 1}},
        )
    )
    items.append(
        RubricItem(
            id="action",
            label="Take Action",
            criteria={"keywords": [
                "step in", "intervene", "helped", "support", "stand up", "speak up"
            ]},
            options=["Present"],
            scoring={"score_map": {"Present": 1}, "severity_map": {"Present": 1}},
        )
    )
    return Rubric(
        name="bystander_intervention",
        description="Bystander Intervention Rubric based on Latané & Darley",
        target_agent=target_agent,
        items=items,
        prompt_template="Detect bystander intervention stages",
    )

