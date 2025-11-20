from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


PACS_CHOICES = [
    "Strongly disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly agree",
]


OFC_ITEMS = [
    ("I am very satisfied with how my parent and I talk together.", True),
    ("My parent and I can talk about just about anything.", True),
    ("My parent and I always understand each other’s point of view.", True),
    ("My parent and I often say mean or bad things when we talk.", False),
    ("I find it easy to discuss problems with my parent.", True),
    ("We talk about our feelings or emotions.", True),
    ("My parent and I calmly discuss issues even when we disagree.", True),
    ("My parent often criticizes me or complains when we talk.", False),
    ("My parent and I listen to each other.", True),
    ("We respect each other's opinions when we talk.", True),
]


PFC_ITEMS = [
    ("It is difficult to talk to my parent about personal things.", False),
    ("My parent doesn’t really understand me.", False),
    ("I can’t express my true feelings to my parent.", False),
    ("We often misunderstand each other.", False),
    ("My parent doesn’t take my point of view seriously.", False),
    ("Discussions with my parent usually end up in arguments.", False),
    ("My parent ignores what I have to say.", False),
    ("My parent gets angry when we disagree.", False),
    ("My parent often interrupts me when I am speaking.", False),
    ("Sometimes I keep things to myself because I can't talk to my parent.", False),
]


class PACSQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = []
        for s, pos in OFC_ITEMS:
            questions.append(
                Question(
                    statement=s,
                    dimension="Open Family Communication",
                    preprompt="",
                    choices=PACS_CHOICES,
                    ascending_scale=True if pos else False,
                )
            )
        for s, pos in PFC_ITEMS:
            questions.append(
                Question(
                    statement=s,
                    dimension="Problems in Family Communication",
                    preprompt="",
                    choices=PACS_CHOICES,
                    ascending_scale=False if pos is False else True,
                )
            )
        super().__init__(
            name="PACS",
            description="Parent-Adolescent Communication Scale",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your usual communication with your parent.",
            dimensions=["Open Family Communication", "Problems in Family Communication"],
        )

        
    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        ofc_values: List[float] = []
        pfc_values: List[float] = []
        total_values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                total_values.append(float(value))
                if dim == "Open Family Communication":
                    ofc_values.append(float(value))
                elif dim == "Problems in Family Communication":
                    pfc_values.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "PACS_Total_Sum": _sum(total_values),
            "PACS_Total_Mean": _mean(total_values),
            "PACS_OFC_Sum": _sum(ofc_values),
            "PACS_OFC_Mean": _mean(ofc_values),
            "PACS_PFC_Sum": _sum(pfc_values),
            "PACS_PFC_Mean": _mean(pfc_values),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

