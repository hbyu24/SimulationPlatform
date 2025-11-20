from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT5_TRUE = [
    "Not at all true",
    "Slightly true",
    "Somewhat true",
    "Mostly true",
    "Completely true",
]


class PerceivedSafetyQuestionnaire(QuestionnaireBase):
    def __init__(self):
        items = [
            "I feel safe when I am in my class.",
            "I feel that other students respect me in my class.",
            "I am not worried about being hurt by other students in my class.",
        ]
        questions: List[Question] = []
        for t in items:
            questions.append(
                Question(
                    statement=t,
                    dimension="Perceived Safety",
                    preprompt="",
                    choices=LIKERT5_TRUE,
                    ascending_scale=True,
                )
            )
        super().__init__(
            name="PerceivedSafety",
            description="Perceived Safety (3 items)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following items.",
            questions=questions,
            preprompt="Please indicate how true each statement is for you.",
            dimensions=["Perceived Safety"],
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
            "PerceivedSafety_Sum": _sum(vals),
            "PerceivedSafety_Mean": _mean(vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
