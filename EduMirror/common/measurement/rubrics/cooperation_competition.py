from typing import Optional, List
from ..rater import Rubric, RubricItem

def get_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []
    items.append(
        RubricItem(
            id="coop_help",
            label="Cooperative Help",
            criteria={"keywords": ["help", "support", "assist", "work together", "team up", "collaborate"]},
            options=["cooperative"],
            scoring={"score_map": {"cooperative": 1.0}, "severity_map": {"cooperative": 1}},
        )
    )
    items.append(
        RubricItem(
            id="coop_encourage",
            label="Encouraging Others",
            criteria={"keywords": ["encourage", "cheer", "motivate", "positive feedback"]},
            options=["cooperative"],
            scoring={"score_map": {"cooperative": 1.0}, "severity_map": {"cooperative": 1}},
        )
    )
    items.append(
        RubricItem(
            id="compete_brag",
            label="Competitive Bragging",
            criteria={"keywords": ["beat", "win", "better than", "outperform", "top", "number one"]},
            options=["competitive"],
            scoring={"score_map": {"competitive": 1.0}, "severity_map": {"competitive": 1}},
        )
    )
    items.append(
        RubricItem(
            id="compete_refuse",
            label="Refusing Cooperation",
            criteria={"keywords": ["refuse", "not share", "do it alone", "solo", "mine", "my own"]},
            options=["competitive"],
            scoring={"score_map": {"competitive": 1.0}, "severity_map": {"competitive": 1}},
        )
    )
    return Rubric(
        name="cooperation_competition",
        description="Detect cooperative versus competitive behaviors",
        target_agent=target_agent,
        items=items,
        prompt_template="Classify behaviors as cooperative or competitive",
    )