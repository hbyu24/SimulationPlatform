from typing import Optional, List
from ..rater import Rubric, RubricItem

def get_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []
    items.append(
        RubricItem(
            id="specific",
            label="Specific",
            criteria={"keywords": ["who", "what", "where", "when", "clear", "precise"]},
            options=["Not at all", "Partially", "Mostly", "Fully"],
            scoring={"score_map": {"Not at all": 1.0, "Partially": 2.0, "Mostly": 3.0, "Fully": 4.0}, "severity_map": {"Not at all": 1, "Partially": 1, "Mostly": 1, "Fully": 1}},
        )
    )
    items.append(
        RubricItem(
            id="measurable",
            label="Measurable",
            criteria={"keywords": ["percent", "accuracy", "times", "frequency", "observable", "track"]},
            options=["Not at all", "Partially", "Mostly", "Fully"],
            scoring={"score_map": {"Not at all": 1.0, "Partially": 2.0, "Mostly": 3.0, "Fully": 4.0}, "severity_map": {"Not at all": 1, "Partially": 1, "Mostly": 1, "Fully": 1}},
        )
    )
    items.append(
        RubricItem(
            id="achievable",
            label="Achievable",
            criteria={"keywords": ["realistic", "attainable", "feasible", "resources", "supports"]},
            options=["Not at all", "Partially", "Mostly", "Fully"],
            scoring={"score_map": {"Not at all": 1.0, "Partially": 2.0, "Mostly": 3.0, "Fully": 4.0}, "severity_map": {"Not at all": 1, "Partially": 1, "Mostly": 1, "Fully": 1}},
        )
    )
    return Rubric(
        name="smart_goal_quality",
        description="Assess SMART goal quality across Specific, Measurable, Achievable",
        target_agent=target_agent,
        items=items,
        prompt_template="Rate SMART goal quality",
    )
