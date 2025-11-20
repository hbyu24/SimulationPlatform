from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


BPNS_CHOICES = [
    "Not at all true",
    "Slightly true",
    "Somewhat true",
    "Mostly true",
    "Completely true",
]


AUTONOMY_ITEMS = [
    ("I feel like I am free to decide for myself how to live my life.", True),
    ("I feel pressured in my life.", False),
    ("I generally feel free to express my ideas and opinions.", True),
    ("I feel like I am doing what I really want to do in my life.", True),
    ("There are many things I have to do that I don't choose to do.", False),
    ("I feel like I can pretty much be myself in my daily situations.", True),
]


COMPETENCE_ITEMS = [
    ("I feel confident that I can do things well.", True),
    ("People I know tell me I am good at what I do.", True),
    ("I often do not feel very capable.", False),
    ("Most days I feel a sense of accomplishment from what I do.", True),
    ("I often feel like I am not doing well.", False),
    ("I feel effective and capable in my activities.", True),
]


class BPNSGQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = []
        for s, asc in AUTONOMY_ITEMS:
            questions.append(
                Question(
                    statement=s,
                    dimension="Autonomy",
                    preprompt="",
                    choices=BPNS_CHOICES,
                    ascending_scale=asc,
                )
            )
        for s, asc in COMPETENCE_ITEMS:
            questions.append(
                Question(
                    statement=s,
                    dimension="Competence",
                    preprompt="",
                    choices=BPNS_CHOICES,
                    ascending_scale=asc,
                )
            )
        super().__init__(
            name="BPNS-G",
            description="Basic Psychological Needs Scale - General (Autonomy & Competence)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please indicate how true each statement is for you.",
            dimensions=["Autonomy", "Competence"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        autonomy_values: List[float] = []
        competence_values: List[float] = []
        total_values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                total_values.append(float(value))
                if dim == "Autonomy":
                    autonomy_values.append(float(value))
                elif dim == "Competence":
                    competence_values.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "BPNSG_Total_Sum": _sum(total_values),
            "BPNSG_Total_Mean": _mean(total_values),
            "BPNSG_Autonomy_Sum": _sum(autonomy_values),
            "BPNSG_Autonomy_Mean": _mean(autonomy_values),
            "BPNSG_Competence_Sum": _sum(competence_values),
            "BPNSG_Competence_Mean": _mean(competence_values),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
