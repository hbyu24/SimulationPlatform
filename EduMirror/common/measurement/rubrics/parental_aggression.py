from typing import Optional, List
from ..rater import Rubric, RubricItem


def get_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []
    items.append(
        RubricItem(
            id="blaming_fault",
            label="Blaming",
            criteria={"keywords": ["fault", "bad teaching", "waste of money", "lazy", "your teaching", "not pushing"]},
            options=["blaming"],
            scoring={"score_map": {"blaming": 1.0}, "severity_map": {"blaming": 2}},
        )
    )
    items.append(
        RubricItem(
            id="collaboration_support",
            label="Collaboration",
            criteria={"keywords": ["help", "support", "work together", "strategy", "plan", "solve together"]},
            options=["collaboration"],
            scoring={"score_map": {"collaboration": 1.0}, "severity_map": {"collaboration": 1}},
        )
    )
    return Rubric(
        name="parental_aggression",
        description="Detect parental blaming versus collaboration in conference",
        target_agent=target_agent,
        items=items,
        prompt_template="Classify parental behaviors as blaming or collaboration",
    )

