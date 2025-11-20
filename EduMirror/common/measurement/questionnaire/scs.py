from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT5 = [
    "Strongly disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly agree",
]


class SCSQuestionnaire(QuestionnaireBase):
    def __init__(self):
        items = [
            "I feel close to people at this school.",
            "I feel like I am part of this school.",
            "I am happy to be at this school.",
            "I feel like I belong at this school.",
            "The teachers at this school treat me fairly.",
            "I feel safe in my school.",
            "I can talk to my teachers about things that bother me.",
            "There is a teacher or some other adult at school who really cares about me.",
        ]
        questions: List[Question] = []
        for t in items:
            questions.append(
                Question(
                    statement=t,
                    dimension="School Connectedness",
                    preprompt="",
                    choices=LIKERT5,
                    ascending_scale=True,
                )
            )
        super().__init__(
            name="SCS",
            description="School Connectedness Scale (8 items)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following items.",
            questions=questions,
            preprompt="Please indicate how much you agree.",
            dimensions=["School Connectedness"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        return super().process_answer(player_name, answer_text, question)

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            if isinstance(value, (int, float)):
                vals.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "SCS_Sum": _sum(vals),
            "SCS_Mean": _mean(vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
