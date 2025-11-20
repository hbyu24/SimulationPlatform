from typing import Any, Dict, List, Optional

from common.measurement.rater import Rubric, RubricItem


def build_restorative_vs_punitive_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = [
        RubricItem(
            id="fairness_perception",
            label="Fairness Perception",
            criteria={"keywords": ["unfair", "not fair", "no one cares", "bias"]},
            options=["Low", "Medium", "High"],
            scoring={
                "score_map": {"Low": 1, "Medium": 2, "High": 3},
                "severity_map": {"Low": 1, "Medium": 2, "High": 3},
            },
        ),
        RubricItem(
            id="empathy_expression",
            label="Empathy Expression",
            criteria={"keywords": ["sorry", "apologize", "understand", "I hear you", "I listened"]},
            options=["Yes", "No"],
            scoring={"score_map": {"Yes": 1, "No": 0}, "severity_map": {"Yes": 1, "No": 0}},
        ),
        RubricItem(
            id="punishment_severity",
            label="Punishment Severity",
            criteria={"keywords": ["suspension", "detention", "warning"]},
            options=["None", "Detention", "Suspension"],
            scoring={"score_map": {"None": 0, "Detention": 1, "Suspension": 2}, "severity_map": {"None": 0, "Detention": 1, "Suspension": 2}},
        ),
    ]
    prompt_template = "Analyze conversation events and assign rubric options based on keyword presence."
    return Rubric(
        name="restorative_vs_punitive_rubric",
        description="Rubric comparing restorative vs punitive signals",
        target_agent=target_agent,
        items=items,
        prompt_template=prompt_template,
    )

