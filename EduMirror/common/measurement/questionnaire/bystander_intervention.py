from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_5 = [
    "Never",
    "Rarely",
    "Sometimes",
    "Often",
    "Always",
]


class BystanderInterventionQuestionnaire(QuestionnaireBase):
    def __init__(self):
        positive_items = [
            "I would tell the bully to stop.",
            "I would tell a teacher or adult at school about the bullying.",
            "I would encourage other students to help stop the bullying.",
            "I would comfort the student who was bullied.",
            "I would try to help the bullied student get away.",
            "I would try to get help for the bullied student.",
            "I would talk to the bullied student afterwards to see if they are okay.",
            "I would ask others to help me stop the bullying.",
        ]
        negative_items = [
            "I would join in the bullying.",
            "I would laugh at the student being bullied.",
            "I would do nothing.",
            "I would walk away from the bullying.",
            "I would encourage the bully.",
            "I would stay and watch the bullying.",
            "I would tell my friends what happened.",
            "I would avoid being around the bully in the future.",
        ]

        questions: List[Question] = []
        for s in positive_items:
            questions.append(
                Question(
                    statement=s,
                    dimension="Bystander Positive",
                    preprompt="",
                    choices=LIKERT_5,
                    ascending_scale=True,
                )
            )
        for s in negative_items:
            questions.append(
                Question(
                    statement=s,
                    dimension="Bystander Negative",
                    preprompt="",
                    choices=LIKERT_5,
                    ascending_scale=False,
                )
            )

        super().__init__(
            name="BIBM",
            description="Bystander Intervention in Bullying Measure",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="How likely are you to do the following?",
            dimensions=["Bystander Positive", "Bystander Negative"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        return super().process_answer(player_name, answer_text, question)

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        pos_vals: List[float] = []
        neg_vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                if dim == "Bystander Positive":
                    pos_vals.append(float(value))
                elif dim == "Bystander Negative":
                    neg_vals.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        total_vals = pos_vals + neg_vals
        return {
            "BIBM_Total_Sum": _sum(total_vals),
            "BIBM_Total_Mean": _mean(total_vals),
            "BIBM_Positive_Sum": _sum(pos_vals),
            "BIBM_Positive_Mean": _mean(pos_vals),
            "BIBM_Negative_Sum": _sum(neg_vals),
            "BIBM_Negative_Mean": _mean(neg_vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
