from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


PANAS_CHOICES = [
    "Very slightly or not at all",
    "A little",
    "Moderately",
    "Quite a bit",
    "Extremely",
]


class PANASXQuestionnaire(QuestionnaireBase):
    def __init__(self):
        guilt_words = [
            "Guilty",
            "Ashamed",
            "Blameworthy",
            "Angry at self",
            "Disgusted with self",
            "Dissatisfied with self",
        ]
        fear_words = [
            "Afraid",
            "Scared",
            "Frightened",
            "Nervous",
            "Jittery",
            "Shaky",
        ]

        questions: List[Question] = []
        for w in guilt_words:
            questions.append(
                Question(
                    statement=f"Indicate to what extent you have felt this way during the past week: {w}",
                    dimension="Guilt",
                    preprompt="",
                    choices=PANAS_CHOICES,
                    ascending_scale=True,
                )
            )
        for w in fear_words:
            questions.append(
                Question(
                    statement=f"Indicate to what extent you have felt this way during the past week: {w}",
                    dimension="Fear",
                    preprompt="",
                    choices=PANAS_CHOICES,
                    ascending_scale=True,
                )
            )

        super().__init__(
            name="PANAS-X",
            description="PANAS-X selected subscales: Guilt and Fear",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please indicate how you have felt during the past week.",
            dimensions=["Guilt", "Fear"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        return super().process_answer(player_name, answer_text, question)

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        guilt_vals: List[float] = []
        fear_vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                if dim == "Guilt":
                    guilt_vals.append(float(value))
                elif dim == "Fear":
                    fear_vals.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        total_vals = guilt_vals + fear_vals
        return {
            "PANAS_X_Total_Sum": _sum(total_vals),
            "PANAS_X_Total_Mean": _mean(total_vals),
            "PANAS_X_Guilt_Sum": _sum(guilt_vals),
            "PANAS_X_Guilt_Mean": _mean(guilt_vals),
            "PANAS_X_Fear_Sum": _sum(fear_vals),
            "PANAS_X_Fear_Mean": _mean(fear_vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

