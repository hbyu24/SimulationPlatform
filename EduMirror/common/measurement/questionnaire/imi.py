from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_7 = [
    "Not at all true",
    "Not true",
    "Somewhat not true",
    "Neutral",
    "Somewhat true",
    "True",
    "Very true",
]


class IMIQuestionnaire(QuestionnaireBase):
    def __init__(self):
        interest_items = [
            ("I enjoyed doing this activity very much.", True),
            ("This activity was fun to do.", True),
            ("I thought this activity was very interesting.", True),
            ("This activity was boring.", False),
            ("This activity did not hold my attention at all.", False),
            ("I would describe this activity as very enjoyable.", True),
            ("While I was doing this activity, I was thinking about how much I enjoyed it.", True),
            ("This activity was not enjoyable.", False),
        ]
        choice_items = [
            ("I believe I had some choice about doing this activity.", True),
            ("I felt like it was not my own choice to do this activity.", False),
            ("I felt like I had to do this activity.", False),
            ("I did this activity because I wanted to.", True),
            ("I felt very pressured while doing this activity.", False),
            ("I was free to do whatever I wanted during this activity.", True),
            ("I did this activity because I had no choice.", False),
        ]
        questions: List[Question] = []
        for text, asc in interest_items:
            questions.append(
                Question(
                    statement=text,
                    dimension="Interest/Enjoyment",
                    preprompt="",
                    choices=LIKERT_7,
                    ascending_scale=asc,
                )
            )
        for text, asc in choice_items:
            questions.append(
                Question(
                    statement=text,
                    dimension="Perceived Choice",
                    preprompt="",
                    choices=LIKERT_7,
                    ascending_scale=asc,
                )
            )
        super().__init__(
            name="IMI",
            description="Intrinsic Motivation Inventory (Interest/Enjoyment & Perceived Choice)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your experience with the target activity.",
            dimensions=["Interest/Enjoyment", "Perceived Choice"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        interest_vals: List[float] = []
        choice_vals: List[float] = []
        total_vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                total_vals.append(float(value))
                if dim == "Interest/Enjoyment":
                    interest_vals.append(float(value))
                elif dim == "Perceived Choice":
                    choice_vals.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "IMI_Total_Sum": _sum(total_vals),
            "IMI_Total_Mean": _mean(total_vals),
            "IMI_Interest_Sum": _sum(interest_vals),
            "IMI_Interest_Mean": _mean(interest_vals),
            "IMI_Choice_Sum": _sum(choice_vals),
            "IMI_Choice_Mean": _mean(choice_vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
