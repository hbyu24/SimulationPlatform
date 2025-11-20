from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_5 = [
    "Not at all true about me",
    "Hardly ever true",
    "Sometimes true",
    "Most of the time true",
    "Always true about me",
]


class LSDQQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(statement="I am lonely at school.", dimension="Loneliness", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I feel left out of things at school.", dimension="Loneliness", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I have nobody to talk to at school.", dimension="Loneliness", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I am unhappy being so alone.", dimension="Loneliness", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="Other kids seem to have more friends than me.", dimension="Social Dissatisfaction", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I feel alone at school.", dimension="Loneliness", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I feel that I do not have any friends.", dimension="Social Dissatisfaction", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I feel left out from the group of kids at school.", dimension="Social Dissatisfaction", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I do not have anyone to play with at school.", dimension="Social Dissatisfaction", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I wish I had more friends.", dimension="Social Dissatisfaction", preprompt="", choices=LIKERT_5, ascending_scale=True),
        ]

        super().__init__(
            name="LSDQ",
            description="Loneliness and Social Dissatisfaction Questionnaire (subset)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your current feelings and thoughts.",
            dimensions=["Loneliness", "Social Dissatisfaction"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        lon_values: List[float] = []
        diss_values: List[float] = []
        total_values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                total_values.append(float(value))
                if dim == "Loneliness":
                    lon_values.append(float(value))
                elif dim == "Social Dissatisfaction":
                    diss_values.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "LSDQ_Total_Sum": _sum(total_values),
            "LSDQ_Total_Mean": _mean(total_values),
            "LSDQ_Loneliness_Mean": _mean(lon_values),
            "LSDQ_SocialDissatisfaction_Mean": _mean(diss_values),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

