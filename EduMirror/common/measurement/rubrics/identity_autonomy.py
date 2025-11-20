from typing import Optional, List
from ..rater import Rubric, RubricItem


def get_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []

    items.append(
        RubricItem(
            id="fusion_soulmate",
            label="Identity Fusion: Soul Mate",
            criteria={"keywords": ["soul mate", "my soulmate"]},
            options=["identity_fusion"],
            scoring={"score_map": {"identity_fusion": 1.0}, "severity_map": {"identity_fusion": 2}},
        )
    )
    items.append(
        RubricItem(
            id="fusion_self_part",
            label="Identity Fusion: Self Merged",
            criteria={"keywords": ["part of who i am", "part of me", "my identity"]},
            options=["identity_fusion"],
            scoring={"score_map": {"identity_fusion": 1.0}, "severity_map": {"identity_fusion": 2}},
        )
    )
    items.append(
        RubricItem(
            id="fusion_criticize_me",
            label="Identity Fusion: Criticism Felt Personal",
            criteria={"keywords": ["criticize my idol", "criticize leo", "attacking me", "insulting me"]},
            options=["identity_fusion"],
            scoring={"score_map": {"identity_fusion": 1.0}, "severity_map": {"identity_fusion": 1}},
        )
    )
    items.append(
        RubricItem(
            id="fusion_true_fan",
            label="Identity Fusion: True Fan Pressure",
            criteria={"keywords": ["true fan", "prove loyalty", "fan club"]},
            options=["identity_fusion"],
            scoring={"score_map": {"identity_fusion": 1.0}, "severity_map": {"identity_fusion": 1}},
        )
    )
    items.append(
        RubricItem(
            id="fusion_mysterious_comm",
            label="Identity Fusion: Mysterious Communication",
            criteria={"keywords": ["communicating in mysterious ways", "mysterious ways"]},
            options=["identity_fusion"],
            scoring={"score_map": {"identity_fusion": 1.0}, "severity_map": {"identity_fusion": 1}},
        )
    )

    items.append(
        RubricItem(
            id="rational_pros_cons",
            label="Rational Decision: Pros and Cons",
            criteria={"keywords": ["pros and cons", "weigh", "weighing"]},
            options=["rational_decision"],
            scoring={"score_map": {"rational_decision": 1.0}, "severity_map": {"rational_decision": 1}},
        )
    )
    items.append(
        RubricItem(
            id="rational_budget",
            label="Rational Decision: Budgeting",
            criteria={"keywords": ["budget", "save money", "afford", "expensive"]},
            options=["rational_decision"],
            scoring={"score_map": {"rational_decision": 1.0}, "severity_map": {"rational_decision": 1}},
        )
    )
    items.append(
        RubricItem(
            id="rational_values",
            label="Rational Decision: Own Values",
            criteria={"keywords": ["my values", "based on my values", "principles"]},
            options=["rational_decision"],
            scoring={"score_map": {"rational_decision": 1.0}, "severity_map": {"rational_decision": 1}},
        )
    )
    items.append(
        RubricItem(
            id="rational_evidence",
            label="Rational Decision: Evidence Based",
            criteria={"keywords": ["evidence", "facts", "information", "alternative"]},
            options=["rational_decision"],
            scoring={"score_map": {"rational_decision": 1.0}, "severity_map": {"rational_decision": 1}},
        )
    )
    items.append(
        RubricItem(
            id="rational_change_mind",
            label="Rational Decision: Willing to Change",
            criteria={"keywords": ["change my mind", "change opinion", "reconsider"]},
            options=["rational_decision"],
            scoring={"score_map": {"rational_decision": 1.0}, "severity_map": {"rational_decision": 1}},
        )
    )

    return Rubric(
        name="identity_autonomy",
        description="Detect identity fusion versus rational decision-making behaviors",
        target_agent=target_agent,
        items=items,
        prompt_template="Classify behaviors indicating identity fusion or rational decision-making",
    )

