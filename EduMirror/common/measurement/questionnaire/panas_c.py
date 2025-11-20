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


class PANASCQuestionnaire(QuestionnaireBase):
    def __init__(self):
        words_pa = [
            "Interested", "Excited", "Enthusiastic", "Proud", "Active",
            "Strong", "Energetic", "Happy", "Cheerful", "Delighted", "Calm",
        ]
        words_na = [
            "Sad", "Frightened", "Scared", "Ashamed", "Jittery", "Upset",
            "Nervous", "Guilty", "Afraid", "Disgusted", "Angry", "Miserable",
            "Alone", "Blue", "Sleepy", "Bashful",
        ]

        statements = words_pa + words_na
        questions: List[Question] = []
        for w in statements:
            dim = "Positive Affect" if w in words_pa else "Negative Affect"
            questions.append(
                Question(
                    statement=f"How much have you felt this way during the past week? {w}",
                    dimension=dim,
                    preprompt="",
                    choices=PANAS_CHOICES,
                    ascending_scale=True,
                )
            )

        super().__init__(
            name="PANAS-C",
            description="Positive and Negative Affect Schedule for Children (27-item version)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your feelings during the past week.",
            dimensions=["Positive Affect", "Negative Affect"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        return super().process_answer(player_name, answer_text, question)

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        pa_vals: List[float] = []
        na_vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                if dim == "Positive Affect":
                    pa_vals.append(float(value))
                elif dim == "Negative Affect":
                    na_vals.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        total_vals = pa_vals + na_vals
        return {
            "PANAS_C_Total_Sum": _sum(total_vals),
            "PANAS_C_Total_Mean": _mean(total_vals),
            "PANAS_C_PA_Sum": _sum(pa_vals),
            "PANAS_C_PA_Mean": _mean(pa_vals),
            "PANAS_C_NA_Sum": _sum(na_vals),
            "PANAS_C_NA_Mean": _mean(na_vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
