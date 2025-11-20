from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


AMS_CHOICES = [
    "Does not correspond at all",
    "Corresponds a little",
    "Corresponds moderately",
    "Corresponds a lot",
    "Corresponds exactly",
]


class AMSQuestionnaire(QuestionnaireBase):
    def __init__(self):
        intrinsic_items = [
            "Because I experience pleasure and satisfaction while learning new things.",
            "Because I enjoy trying to understand new concepts.",
            "For the satisfaction I feel when I am improving my abilities.",
            "For the pleasure I experience when I discover new things never seen before.",
            "Because what I learn matters to me.",
        ]
        extrinsic_items = [
            "Because I am supposed to go to school.",
            "Because my parents/teachers say I have to.",
            "To get a diploma so I can find a better job later on.",
            "Because otherwise I would have problems.",
            "To avoid being punished or criticized.",
        ]

        questions: List[Question] = []
        for s in intrinsic_items:
            questions.append(
                Question(
                    statement=s,
                    dimension="Intrinsic Motivation",
                    preprompt="",
                    choices=AMS_CHOICES,
                    ascending_scale=True,
                )
            )
        for s in extrinsic_items:
            questions.append(
                Question(
                    statement=s,
                    dimension="Extrinsic Motivation - External Regulation",
                    preprompt="",
                    choices=AMS_CHOICES,
                    ascending_scale=True,
                )
            )

        super().__init__(
            name="AMS",
            description="Academic Motivation Scale (selected dimensions)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Indicate to what extent each statement corresponds to your reasons for studying.",
            dimensions=["Intrinsic Motivation", "Extrinsic Motivation - External Regulation"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        intrinsic_vals: List[float] = []
        extrinsic_vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                if dim == "Intrinsic Motivation":
                    intrinsic_vals.append(float(value))
                elif dim == "Extrinsic Motivation - External Regulation":
                    extrinsic_vals.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        total_vals = intrinsic_vals + extrinsic_vals
        return {
            "AMS_Total_Sum": _sum(total_vals),
            "AMS_Total_Mean": _mean(total_vals),
            "AMS_Intrinsic_Sum": _sum(intrinsic_vals),
            "AMS_Intrinsic_Mean": _mean(intrinsic_vals),
            "AMS_Extrinsic_ER_Sum": _sum(extrinsic_vals),
            "AMS_Extrinsic_ER_Mean": _mean(extrinsic_vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

