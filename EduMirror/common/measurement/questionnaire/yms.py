from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


YMS_CHOICES = [
    "Strongly Disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly Agree",
]


class YMSQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="When you grow up, do you think having a lot of money is important?",
                dimension="Materialism",
                preprompt="",
                choices=YMS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I admire kids who have a lot of things.",
                dimension="Materialism",
                preprompt="",
                choices=YMS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I would rather have lots of things than lots of friends.",
                dimension="Materialism",
                preprompt="",
                choices=YMS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="Kids who have more things are happier.",
                dimension="Materialism",
                preprompt="",
                choices=YMS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="When I want something I can't have, I get upset.",
                dimension="Materialism",
                preprompt="",
                choices=YMS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I like to own the best brands.",
                dimension="Materialism",
                preprompt="",
                choices=YMS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I really enjoy shopping and buying new things.",
                dimension="Materialism",
                preprompt="",
                choices=YMS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="Having expensive things makes people happy.",
                dimension="Materialism",
                preprompt="",
                choices=YMS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I feel bad when my friends have things I don't.",
                dimension="Materialism",
                preprompt="",
                choices=YMS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I like to have more material possessions than other kids.",
                dimension="Materialism",
                preprompt="",
                choices=YMS_CHOICES,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="YMS",
            description="Youth Materialism Scale (10-item)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your current feelings and thoughts.",
            dimensions=["Materialism"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            if isinstance(value, (int, float)):
                values.append(float(value))
        total_sum = float(sum(values)) if values else float("nan")
        total_mean = float(sum(values) / len(values)) if values else float("nan")
        return {
            "YMS_Total_Sum": total_sum,
            "YMS_Total_Mean": total_mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

