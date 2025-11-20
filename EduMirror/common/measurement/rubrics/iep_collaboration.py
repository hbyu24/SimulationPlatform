from typing import Optional, List
from ..rater import Rubric, RubricItem

def get_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []
    items.append(
        RubricItem(
            id="active_listening",
            label="Active Listening",
            criteria={"keywords": ["listen", "understand", "paraphrase", "summarize", "let me make sure I understand", "clarify"]},
            options=["Rarely", "Occasionally", "Often", "Consistently"],
            scoring={"score_map": {"Rarely": 1.0, "Occasionally": 2.0, "Often": 3.0, "Consistently": 4.0}, "severity_map": {"Rarely": 1, "Occasionally": 1, "Often": 1, "Consistently": 1}},
        )
    )
    items.append(
        RubricItem(
            id="goal_alignment",
            label="Goal Alignment",
            criteria={"keywords": ["shared goal", "work together", "both want", "consensus", "align"]},
            options=["Rarely", "Occasionally", "Often", "Consistently"],
            scoring={"score_map": {"Rarely": 1.0, "Occasionally": 2.0, "Often": 3.0, "Consistently": 4.0}, "severity_map": {"Rarely": 1, "Occasionally": 1, "Often": 1, "Consistently": 1}},
        )
    )
    items.append(
        RubricItem(
            id="student_centeredness",
            label="Student-Centeredness",
            criteria={"keywords": ["student needs", "accommodation", "support", "plan", "strategy", "adjust environment"]},
            options=["Rarely", "Occasionally", "Often", "Consistently"],
            scoring={"score_map": {"Rarely": 1.0, "Occasionally": 2.0, "Often": 3.0, "Consistently": 4.0}, "severity_map": {"Rarely": 1, "Occasionally": 1, "Often": 1, "Consistently": 1}},
        )
    )
    return Rubric(
        name="iep_collaboration",
        description="Assess collaboration quality in IEP meetings",
        target_agent=target_agent,
        items=items,
        prompt_template="Rate IEP collaboration across Active Listening, Goal Alignment, Student-Centeredness",
    )
