from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_5 = [
    "Strongly disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly agree",
]


class MVSShortQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="I admire people who own expensive homes, cars, and clothes.",
                dimension="Success",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I often compare what I own with what others own.",
                dimension="Centrality",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I like to own things that impress people.",
                dimension="Centrality",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="The things I own say a lot about how well I’m doing in life.",
                dimension="Success",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I like a lot of luxury in my life.",
                dimension="Success",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I sometimes wish I could afford more than I actually can.",
                dimension="Centrality",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="My life would be better if I owned certain things I don’t have.",
                dimension="Happiness",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="Buying things gives me a lot of pleasure.",
                dimension="Happiness",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I’d be happier if I could afford to buy more things.",
                dimension="Happiness",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="MVS-Short",
            description="Material Values Scale – Short Form",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please indicate how much you agree or disagree with each statement.",
            dimensions=["Success", "Centrality", "Happiness"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        success_vals: List[float] = []
        centrality_vals: List[float] = []
        happiness_vals: List[float] = []
        total_vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                v = float(value)
                total_vals.append(v)
                if dim == "Success":
                    success_vals.append(v)
                elif dim == "Centrality":
                    centrality_vals.append(v)
                elif dim == "Happiness":
                    happiness_vals.append(v)
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "MVS_Short_Total_Sum": _sum(total_vals),
            "MVS_Short_Total_Mean": _mean(total_vals),
            "MVS_Short_Success_Mean": _mean(success_vals),
            "MVS_Short_Centrality_Mean": _mean(centrality_vals),
            "MVS_Short_Happiness_Mean": _mean(happiness_vals),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
