from typing import Optional, List
from ..rater import Rubric, RubricItem


def get_fbs_rubric(target_agent: Optional[str] = None) -> Rubric:
    items: List[RubricItem] = []

    # Physical Bullying
    items.append(
        RubricItem(
            id="fbs_physical_hit_kick_push",
            label="Physical Bullying: hit/kick/push",
            criteria={"keywords": ["hit", "kick", "push", "shove"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 3}},
        )
    )
    items.append(
        RubricItem(
            id="fbs_physical_threat_force",
            label="Physical Bullying: threat/force",
            criteria={"keywords": ["threat", "force", "forced", "intimidate"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 3}},
        )
    )

    # Verbal Bullying
    items.append(
        RubricItem(
            id="fbs_verbal_tease_mean",
            label="Verbal Bullying: teasing (mean/hurtful)",
            criteria={"keywords": ["tease", "taunt", "mean", "hurtful"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 2}},
        )
    )
    items.append(
        RubricItem(
            id="fbs_verbal_name_calling",
            label="Verbal Bullying: name-calling",
            criteria={"keywords": ["name", "call", "insult", "mock", "humiliate"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 2}},
        )
    )

    # Social/Relational Bullying
    items.append(
        RubricItem(
            id="fbs_social_left_out",
            label="Relational Bullying: deliberate exclusion",
            criteria={"keywords": ["left out", "exclude", "excluded", "no invite"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 2}},
        )
    )
    items.append(
        RubricItem(
            id="fbs_social_rumor_spread",
            label="Relational Bullying: rumor spreading",
            criteria={"keywords": ["rumor", "spread", "gossip"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 2}},
        )
    )

    # Covert/Indirect Bullying
    items.append(
        RubricItem(
            id="fbs_covert_ignore_exclude",
            label="Covert Bullying: ignore/exclude on purpose",
            criteria={"keywords": ["ignore", "excluded", "on purpose"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 1}},
        )
    )
    items.append(
        RubricItem(
            id="fbs_covert_nasty_notes_msgs",
            label="Covert Bullying: nasty notes/messages",
            criteria={"keywords": ["nasty note", "nasty", "sms", "email", "message"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 1}},
        )
    )

    # Cyber Bullying
    items.append(
        RubricItem(
            id="fbs_cyber_online_bully",
            label="Cyber Bullying: via internet/phone/technology",
            criteria={"keywords": ["online", "internet", "phone", "technology", "social media"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 2}},
        )
    )

    # Victim response (contextual signals)
    items.append(
        RubricItem(
            id="victim_response_signals",
            label="Victim Response (signals)",
            criteria={"keywords": ["cry", "silent", "withdraw", "run away", "avoid", "ignore"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 1}},
        )
    )

    # Bystander actions (supportive or reinforcing)
    items.append(
        RubricItem(
            id="bystander_supportive",
            label="Bystander Supportive Action",
            criteria={"keywords": ["comfort", "support", "help", "report", "tell teacher", "stop"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 1}},
        )
    )
    items.append(
        RubricItem(
            id="bystander_reinforcing",
            label="Bystander Reinforcing Action",
            criteria={"keywords": ["laugh", "cheer", "join in", "encourage"]},
            options=["present"],
            scoring={"score_map": {"present": 1.0}, "severity_map": {"present": 1}},
        )
    )

    return Rubric(
        name="fbs",
        description="Forms of Bullying Scale aligned categories via keyword detection",
        target_agent=target_agent,
        items=items,
        prompt_template="Detect FBS categories and related context from transcript events",
    )