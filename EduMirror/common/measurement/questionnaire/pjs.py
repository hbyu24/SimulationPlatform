from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT7 = [
    "Strongly disagree",
    "Disagree",
    "Slightly disagree",
    "Neutral",
    "Slightly agree",
    "Agree",
    "Strongly agree",
]


class PJSQuestionnaire(QuestionnaireBase):
    def __init__(self):
        proc_items = [
            "Decisions are made using consistent procedures.",
            "All sides affected by the decision are represented in the decision-making process.",
            "Procedures ensure accurate information is collected for making decisions.",
            "There are opportunities to appeal or challenge decisions.",
            "The concerns of all those affected are considered in decisions.",
            "There are guidelines or standards to ensure consistency in decision-making.",
            "There is useful feedback given regarding decisions and their implementation.",
        ]
        inter_items = [
            "My supervisor considered my viewpoint.",
            "My supervisor suppressed personal biases when making decisions.",
            "My supervisor provided timely feedback about the decision and its implications.",
            "My supervisor treated me with kindness and consideration.",
            "My supervisor showed concern for my rights as an employee.",
            "My supervisor dealt with me in a truthful manner.",
        ]
        questions: List[Question] = []
        for t in proc_items:
            questions.append(
                Question(
                    statement=t,
                    dimension="Procedural Justice",
                    preprompt="",
                    choices=LIKERT7,
                    ascending_scale=True,
                )
            )
        for t in inter_items:
            questions.append(
                Question(
                    statement=t,
                    dimension="Interactional Justice",
                    preprompt="",
                    choices=LIKERT7,
                    ascending_scale=True,
                )
            )
        super().__init__(
            name="PJS",
            description="Perceived Justice Scale (Procedural + Interactional)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following items.",
            questions=questions,
            preprompt="Please respond based on your experience in this incident.",
            dimensions=["Procedural Justice", "Interactional Justice"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        return super().process_answer(player_name, answer_text, question)

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        pj_vals: List[float] = []
        ij_vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                if dim == "Procedural Justice":
                    pj_vals.append(float(value))
                elif dim == "Interactional Justice":
                    ij_vals.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        total_vals = pj_vals + ij_vals
        return {
            "PJS_Total_Sum": _sum(total_vals),
            "PJS_Total_Mean": _mean(total_vals),
            "PJS_Procedural_Sum": _sum(pj_vals),
            "PJS_Procedural_Mean": _mean(pj_vals),
            "PJS_Interactional_Sum": _sum(ij_vals),
            "PJS_Interactional_Mean": _mean(ij_vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
