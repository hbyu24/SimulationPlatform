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


class IncomQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="I often compare myself with others with respect to what I have accomplished in life.",
                dimension="Ability Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="If I want to find out how well I have done something, I compare what I have done with how others have done.",
                dimension="Ability Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I always pay a lot of attention to how I do things compared with how others do things.",
                dimension="Ability Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I often compare how I am doing socially (e.g., social skills) with other people.",
                dimension="Ability Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I often compare how I am doing (e.g., job or school performance) with other people.",
                dimension="Ability Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I am not the type of person who compares often with others.",
                dimension="Ability Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=False,
            ),
            Question(
                statement="If I want to learn more about something, I try to find out what others think about it.",
                dimension="Opinion Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I often like to talk with others about mutual opinions and experiences.",
                dimension="Opinion Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I always like to know what others in a similar situation would do.",
                dimension="Opinion Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I often compare my own opinions with the opinions of others.",
                dimension="Opinion Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="I never consider my situation in light of the situation of others.",
                dimension="Opinion Comparison",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=False,
            ),
        ]

        super().__init__(
            name="INCOM",
            description="Iowa–Netherlands Comparison Orientation Measure",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your current feelings and thoughts.",
            dimensions=["Ability Comparison", "Opinion Comparison"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        ability_values: List[float] = []
        opinion_values: List[float] = []
        total_values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                total_values.append(float(value))
                if dim == "Ability Comparison":
                    ability_values.append(float(value))
                elif dim == "Opinion Comparison":
                    opinion_values.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "INCOM_Total_Sum": _sum(total_values),
            "INCOM_Total_Mean": _mean(total_values),
            "INCOM_Ability_Sum": _sum(ability_values),
            "INCOM_Ability_Mean": _mean(ability_values),
            "INCOM_Opinion_Sum": _sum(opinion_values),
            "INCOM_Opinion_Mean": _mean(opinion_values),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None