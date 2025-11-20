from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


SOBI_CHOICES = [
    "Strongly disagree",
    "Disagree",
    "Slightly disagree",
    "Slightly agree",
    "Agree",
    "Strongly agree",
]


class SOBIPsychologicalStateQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="I feel like an outsider.",
                dimension="Belonging",
                preprompt="",
                choices=SOBI_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I feel as if I don’t fit in.",
                dimension="Belonging",
                preprompt="",
                choices=SOBI_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I feel accepted by people around me.",
                dimension="Belonging",
                preprompt="",
                choices=SOBI_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I feel like I belong.",
                dimension="Belonging",
                preprompt="",
                choices=SOBI_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I feel distant from people around me.",
                dimension="Belonging",
                preprompt="",
                choices=SOBI_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I feel connected with people around me.",
                dimension="Belonging",
                preprompt="",
                choices=SOBI_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I feel uncomfortable with where I am.",
                dimension="Belonging",
                preprompt="",
                choices=SOBI_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I feel understood by others.",
                dimension="Belonging",
                preprompt="",
                choices=SOBI_CHOICES,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="SOBI_PsychologicalState",
            description="Sense of Belonging Instrument – Psychological State",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your current feelings.",
            dimensions=["Belonging"],
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
            "SOBI_Total_Sum": total_sum,
            "SOBI_Total_Mean": total_mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

