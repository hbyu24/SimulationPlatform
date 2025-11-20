from typing import List, Optional

from common.measurement.rater import Rubric, RubricItem


def build_communication_rubrics(target_agent: Optional[str] = None) -> List[Rubric]:
    autonomy_support = Rubric(
        name="AutonomySupport",
        description="Autonomy-supportive communication markers",
        target_agent=target_agent,
        items=[
            RubricItem(
                id="AS_presence",
                label="Autonomy-support language present",
                criteria={"keywords": [
                    "i feel", "my choice", "i want", "free", "support", "understand", "listen", "plan together", "my needs", "feelings"
                ]},
                options=["Present"],
                scoring={"score_map": {"Present": 1}, "severity_map": {"Present": 1}},
            ),
        ],
        prompt_template="",
    )
    authoritarian = Rubric(
        name="AuthoritarianStyle",
        description="Authoritarian/controlling communication markers",
        target_agent=target_agent,
        items=[
            RubricItem(
                id="AT_presence",
                label="Authoritarian language present",
                criteria={"keywords": [
                    "must", "have to", "no choice", "should", "for your future", "cannot", "pressure", "obligation"
                ]},
                options=["Present"],
                scoring={"score_map": {"Present": 1}, "severity_map": {"Present": 2}},
            ),
        ],
        prompt_template="",
    )
    return [autonomy_support, authoritarian]
