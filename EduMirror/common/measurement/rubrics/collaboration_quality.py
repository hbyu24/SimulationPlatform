from typing import List

from common.measurement.rater import Rubric, RubricItem


def get_collaboration_quality_rubric() -> Rubric:
    items: List[RubricItem] = [
        RubricItem(
            id="collaborating",
            label="Collaborating",
            criteria={"keywords": [
                "collaborate",
                "work together",
                "mutual benefit",
                "share information",
                "explore options",
            ]},
            options=["present"],
            scoring={"score_map": {"present": 1}, "severity_map": {"present": 2}},
        ),
        RubricItem(
            id="competing",
            label="Competing",
            criteria={"keywords": [
                "win",
                "insist",
                "my way",
                "not listening",
            ]},
            options=["present"],
            scoring={"score_map": {"present": 1}, "severity_map": {"present": 3}},
        ),
        RubricItem(
            id="avoiding",
            label="Avoiding",
            criteria={"keywords": [
                "avoid",
                "skip",
                "ignore",
                "leave",
            ]},
            options=["present"],
            scoring={"score_map": {"present": 1}, "severity_map": {"present": 2}},
        ),
        RubricItem(
            id="accommodating",
            label="Accommodating",
            criteria={"keywords": [
                "sorry",
                "yield",
                "let you decide",
                "go along",
            ]},
            options=["present"],
            scoring={"score_map": {"present": 1}, "severity_map": {"present": 1}},
        ),
        RubricItem(
            id="compromising",
            label="Compromising",
            criteria={"keywords": [
                "compromise",
                "split the difference",
                "middle ground",
            ]},
            options=["present"],
            scoring={"score_map": {"present": 1}, "severity_map": {"present": 2}},
        ),
    ]
    return Rubric(
        name="CollaborationQuality",
        description="Collaboration Quality Rubric (Thomas-Kilmann modes)",
        target_agent=None,
        items=items,
        prompt_template="",
    )

