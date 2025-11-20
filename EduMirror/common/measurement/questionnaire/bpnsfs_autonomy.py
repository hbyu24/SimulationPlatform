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
    "Completely true",
]


class BPNSFSAutonomyQuestionnaire(QuestionnaireBase):
    def __init__(self):
        satisfaction = [
            "I feel a sense of choice and freedom in the things I undertake.",
            "I feel that my decisions reflect what I really want.",
            "I feel that my choices express who I really am.",
        ]
        frustration = [
            "I feel forced to do many things I wouldn’t choose to do.",
            "I feel pressured to do many things I wouldn’t choose to do.",
            "My daily activities feel like a chain of obligations.",
        ]
        questions: List[Question] = []
        for text in satisfaction:
            questions.append(
                Question(
                    statement=text,
                    dimension="Autonomy Satisfaction",
                    preprompt="",
                    choices=LIKERT_7,
                    ascending_scale=True,
                )
            )
        for text in frustration:
            questions.append(
                Question(
                    statement=text,
                    dimension="Autonomy Frustration",
                    preprompt="",
                    choices=LIKERT_7,
                    ascending_scale=True,
                )
            )
        super().__init__(
            name="BPNSFS-Autonomy",
            description="Basic Psychological Need Satisfaction and Frustration Scale – Autonomy",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please indicate the extent to which each statement applies when interacting with your parents.",
            dimensions=["Autonomy Satisfaction", "Autonomy Frustration"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        sat_vals: List[float] = []
        fru_vals: List[float] = []
        total_vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                total_vals.append(float(value))
                if dim == "Autonomy Satisfaction":
                    sat_vals.append(float(value))
                elif dim == "Autonomy Frustration":
                    fru_vals.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "BPNSFS_Autonomy_Total_Sum": _sum(total_vals),
            "BPNSFS_Autonomy_Total_Mean": _mean(total_vals),
            "BPNSFS_Autonomy_Satisfaction_Sum": _sum(sat_vals),
            "BPNSFS_Autonomy_Satisfaction_Mean": _mean(sat_vals),
            "BPNSFS_Autonomy_Frustration_Sum": _sum(fru_vals),
            "BPNSFS_Autonomy_Frustration_Mean": _mean(fru_vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
