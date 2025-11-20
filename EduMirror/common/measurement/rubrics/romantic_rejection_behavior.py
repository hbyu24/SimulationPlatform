from typing import Optional, List
from ..rater import Rubric, RubricItem


def get_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []
    items.append(
        RubricItem(
            id="hostility_insult",
            label="Hostility: Insults/Attacks",
            criteria={"keywords": ["insult", "rumor", "attack", "humiliate", "loser", "worthless", "hate", "angry"]},
            options=["hostility"],
            scoring={"score_map": {"hostility": 1.0}, "severity_map": {"hostility": 1}},
        )
    )
    items.append(
        RubricItem(
            id="maturity_respect",
            label="Maturity: Respect/Boundaries",
            criteria={"keywords": ["polite", "respect", "boundary", "apologize", "accept", "thank you", "sorry", "move on"]},
            options=["maturity"],
            scoring={"score_map": {"maturity": 1.0}, "severity_map": {"maturity": 1}},
        )
    )
    items.append(
        RubricItem(
            id="obsessiveness_persist",
            label="Obsessiveness: Persist/Push",
            criteria={"keywords": ["persist", "won't accept", "beg", "again", "explain", "prove", "try again", "keep asking"]},
            options=["obsessive"],
            scoring={"score_map": {"obsessive": 1.0}, "severity_map": {"obsessive": 1}},
        )
    )
    return Rubric(
        name="romantic_rejection_behavior",
        description="Detect hostility, maturity, and obsessiveness in romantic rejection dynamics",
        target_agent=target_agent,
        items=items,
        prompt_template="Classify behaviors around romantic rejection into hostility, maturity, or obsessiveness",
    )

