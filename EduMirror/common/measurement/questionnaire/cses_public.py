from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


CSES_CHOICES = [
    "Strongly Disagree",
    "Disagree",
    "Somewhat Disagree",
    "Neutral",
    "Somewhat Agree",
    "Agree",
    "Strongly Agree",
]


class CSESPublicQuestionnaire(QuestionnaireBase):
    def __init__(self, group_placeholder: str = "my school"):
        dim = "Collective Self-Esteem (Public)"
        questions: List[Question] = [
            Question(
                statement=f"Overall, {group_placeholder} is considered good by others.",
                dimension=dim,
                preprompt="",
                choices=CSES_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement=f"Most people consider {group_placeholder}, on the average, to be more respected than other groups.",
                dimension=dim,
                preprompt="",
                choices=CSES_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement=f"In general, others respect the social groups that I am a member of.",
                dimension=dim,
                preprompt="",
                choices=CSES_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement=f"Overall, my social groups are considered worse than other groups.",
                dimension=dim,
                preprompt="",
                choices=CSES_CHOICES,
                ascending_scale=False,
            ),
        ]

        super().__init__(
            name="CSES_Public",
            description="Collective Self-Esteem Scale (Public Subscale)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on perceptions of how others evaluate your group.",
            dimensions=[dim],
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
        mean_val = float(sum(values) / len(values)) if values else float("nan")
        return {
            "CSES_Public_Mean": mean_val,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
