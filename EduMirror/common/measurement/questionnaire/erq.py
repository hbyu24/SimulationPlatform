from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


ERQ_CHOICES = [
    "Strongly disagree",
    "Disagree",
    "Slightly disagree",
    "Neutral",
    "Slightly agree",
    "Agree",
    "Strongly agree",
]


class ERQQuestionnaire(QuestionnaireBase):
    def __init__(self):
        items = [
            (1, "When I want to feel more positive emotion (such as joy or amusement), I change what I’m thinking about.", "Reappraisal"),
            (2, "I keep my emotions to myself.", "Suppression"),
            (3, "When I want to feel less negative emotion (such as sadness or anger), I change what I’m thinking about.", "Reappraisal"),
            (4, "When I am feeling positive emotions, I am careful not to express them.", "Suppression"),
            (5, "When I want to feel less negative emotion, I change the way I’m thinking about the situation.", "Reappraisal"),
            (6, "I control my emotions by not expressing them.", "Suppression"),
            (7, "When I am feeling negative emotions, I make sure not to express them.", "Suppression"),
            (8, "When I want to feel more positive emotion, I change the way I’m thinking about the situation.", "Reappraisal"),
            (9, "I control my emotions by changing the way I think about the situation I’m in.", "Reappraisal"),
            (10, "When I am feeling positive emotions, I am careful not to express them.", "Suppression"),
        ]
        questions: List[Question] = []
        for num, text, dim in items:
            questions.append(
                Question(
                    statement=f"ERQ Item {num}: {text}",
                    dimension=dim,
                    preprompt="",
                    choices=ERQ_CHOICES,
                    ascending_scale=True,
                )
            )

        super().__init__(
            name="ERQ",
            description="Emotion Regulation Questionnaire (Gross & John, 2003)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following items.",
            questions=questions,
            preprompt="Please rate each statement using the 1–7 scale.",
            dimensions=["Reappraisal", "Suppression"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        return super().process_answer(player_name, answer_text, question)

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        reapp_vals: List[float] = []
        supp_vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                if dim == "Reappraisal":
                    reapp_vals.append(float(value))
                elif dim == "Suppression":
                    supp_vals.append(float(value))
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "ERQ_Reappraisal_Mean": _mean(reapp_vals),
            "ERQ_Suppression_Mean": _mean(supp_vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
