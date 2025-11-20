from typing import List, Optional

from common.measurement.rater import Rubric, RubricItem


def create_social_comparison_rubric(target_agent: Optional[str] = "Leo") -> Rubric:
    items: List[RubricItem] = [
        RubricItem(
            id="verbalized_envy",
            label="Verbalized Envy",
            criteria={"keywords": [
                "wish i had",
                "it's not fair",
                "unfair",
                "jealous",
                "i want those",
            ]},
            options=["occurred"],
            scoring={"score_map": {"occurred": 1}, "severity_map": {"occurred": 3}},
        ),
        RubricItem(
            id="depreciation_of_self",
            label="Depreciation of Self",
            criteria={"keywords": [
                "i'm not good",
                "not good at",
                "my shoes are old",
                "can't defend",
                "bad player",
                "embarrassed",
                "hide my shoes",
            ]},
            options=["occurred"],
            scoring={"score_map": {"occurred": 1}, "severity_map": {"occurred": 3}},
        ),
        RubricItem(
            id="focus_on_external",
            label="Focus on External",
            criteria={"keywords": [
                "brand",
                "price",
                "shoes",
                "gear",
                "limited edition",
            ]},
            options=["occurred"],
            scoring={"score_map": {"occurred": 1}, "severity_map": {"occurred": 2}},
        ),
    ]
    return Rubric(
        name="Social Comparison Behavior Rubric",
        description="Measures social comparison behaviors in interactions",
        target_agent=target_agent,
        items=items,
        prompt_template="",
    )


def create_consumer_decision_rubric(target_agent: Optional[str] = "Leo") -> Rubric:
    items: List[RubricItem] = [
        RubricItem(
            id="impulsivity",
            label="Impulsivity",
            criteria={"keywords": [
                "buy now",
                "immediately",
                "right now",
                "just buy",
                "last pair",
            ]},
            options=["very_poor"],
            scoring={"score_map": {"very_poor": 1}, "severity_map": {"very_poor": 4}},
        ),
        RubricItem(
            id="peer_pressure_susceptibility",
            label="Peer Pressure Susceptibility",
            criteria={"keywords": [
                "because kevin",
                "kevin said",
                "he said so",
                "pro duo",
                "you should buy",
            ]},
            options=["very_poor"],
            scoring={"score_map": {"very_poor": 1}, "severity_map": {"very_poor": 4}},
        ),
        RubricItem(
            id="financial_realism",
            label="Financial Realism",
            criteria={"keywords": [
                "savings",
                "budget",
                "afford",
                "computer",
                "expensive",
                "cost",
            ]},
            options=["excellent"],
            scoring={"score_map": {"excellent": 5}, "severity_map": {"excellent": 5}},
        ),
    ]
    return Rubric(
        name="Consumer Decision Quality Rubric",
        description="Rates consumer decision quality in shopping scenario",
        target_agent=target_agent,
        items=items,
        prompt_template="",
    )

