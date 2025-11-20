from typing import Optional, List
from ..rater import Rubric, RubricItem

def get_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []
    items.append(
        RubricItem(
            id="dishonesty",
            label="Dishonesty",
            criteria={"keywords": [
                "lie",
                "lied",
                "not true",
                "pretend",
                "made up",
                "fake",
                "preorder",
                "ordered",
            ]},
            options=["dishonest"],
            scoring={"score_map": {"dishonest": 1.0}, "severity_map": {"dishonest": 1}},
        )
    )
    items.append(
        RubricItem(
            id="aggression",
            label="Aggressive Language",
            criteria={"keywords": [
                "angry",
                "yell",
                "shout",
                "attack",
                "blame",
                "insult",
                "furious",
                "scream",
                "hate",
            ]},
            options=["aggressive"],
            scoring={"score_map": {"aggressive": 1.0}, "severity_map": {"aggressive": 1}},
        )
    )
    items.append(
        RubricItem(
            id="envy_comparison",
            label="Envy/Upward Comparison",
            criteria={"keywords": [
                "envy",
                "jealous",
                "better than",
                "more expensive",
                "new phone",
                "best brands",
                "shopping",
                "expensive",
                "own more",
                "have more",
                "feel bad",
                "can't have",
            ]},
            options=["comparison"],
            scoring={"score_map": {"comparison": 1.0}, "severity_map": {"comparison": 1}},
        )
    )
    return Rubric(
        name="materialism_behaviors",
        description="Detect dishonesty, aggression and materialistic comparison",
        target_agent=target_agent,
        items=items,
        prompt_template="Classify behaviors",
    )

