from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


RSES_CHOICES = [
    "Strongly Disagree",
    "Disagree",
    "Agree",
    "Strongly Agree",
]


class RSESQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="On the whole, I am satisfied with myself.",
                dimension="Self-Esteem",
                preprompt="",
                choices=RSES_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="At times, I think I am no good at all.",
                dimension="Self-Esteem",
                preprompt="",
                choices=RSES_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I feel that I have a number of good qualities.",
                dimension="Self-Esteem",
                preprompt="",
                choices=RSES_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I am able to do things as well as most other people.",
                dimension="Self-Esteem",
                preprompt="",
                choices=RSES_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I feel I do not have much to be proud of.",
                dimension="Self-Esteem",
                preprompt="",
                choices=RSES_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I certainly feel useless at times.",
                dimension="Self-Esteem",
                preprompt="",
                choices=RSES_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I feel that I’m a person of worth, at least on an equal plane with others.",
                dimension="Self-Esteem",
                preprompt="",
                choices=RSES_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I wish I could have more respect for myself.",
                dimension="Self-Esteem",
                preprompt="",
                choices=RSES_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="All in all, I am inclined to feel that I am a failure.",
                dimension="Self-Esteem",
                preprompt="",
                choices=RSES_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I take a positive attitude toward myself.",
                dimension="Self-Esteem",
                preprompt="",
                choices=RSES_CHOICES,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="RSES",
            description="Rosenberg Self-Esteem Scale",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your current feelings and thoughts.",
            dimensions=["Self-Esteem"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        return super().process_answer(player_name, answer_text, question)

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            if isinstance(value, (int, float)):
                values.append(float(value))
        total_sum = float(sum(values)) if values else float("nan")
        total_mean = float(sum(values) / len(values)) if values else float("nan")
        return {
            "RSES_Total_Sum": total_sum,
            "RSES_Total_Mean": total_mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None