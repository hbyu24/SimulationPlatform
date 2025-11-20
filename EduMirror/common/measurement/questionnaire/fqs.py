from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_5 = [
    "I disagree strongly",
    "I disagree",
    "Neutral",
    "I agree",
    "I agree strongly",
]


class FQSQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="My friend and I spend time together often.",
                dimension="Companionship",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="My friend and I like the same things.",
                dimension="Companionship",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="My friend helps me when I am having trouble with something.",
                dimension="Help",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="If I have a problem at school or at home, I can talk to my friend about it.",
                dimension="Help",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="My friend makes me feel safe and secure.",
                dimension="Security",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="My friend makes me feel good about myself.",
                dimension="Security",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="My friend and I can argue easily.",
                dimension="Conflict",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=False,
            ),
            Question(
                statement="My friend and I sometimes get mad at each other.",
                dimension="Conflict",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=False,
            ),
            Question(
                statement="My friend and I feel close to each other.",
                dimension="Closeness",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="FQS",
            description="Friendship Qualities Scale (subset)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your current feelings and thoughts.",
            dimensions=["Companionship", "Help", "Security", "Conflict", "Closeness"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        comp_values: List[float] = []
        help_values: List[float] = []
        sec_values: List[float] = []
        conf_values: List[float] = []
        close_values: List[float] = []
        total_values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                total_values.append(float(value))
                if dim == "Companionship":
                    comp_values.append(float(value))
                elif dim == "Help":
                    help_values.append(float(value))
                elif dim == "Security":
                    sec_values.append(float(value))
                elif dim == "Conflict":
                    conf_values.append(float(value))
                elif dim == "Closeness":
                    close_values.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "FQS_Total_Sum": _sum(total_values),
            "FQS_Total_Mean": _mean(total_values),
            "FQS_Companionship_Mean": _mean(comp_values),
            "FQS_Help_Mean": _mean(help_values),
            "FQS_Security_Mean": _mean(sec_values),
            "FQS_Conflict_Mean": _mean(conf_values),
            "FQS_Closeness_Mean": _mean(close_values),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

