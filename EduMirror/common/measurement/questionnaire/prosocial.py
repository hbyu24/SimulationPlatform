from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


PROSOCIAL_CHOICES = [
    "Not true",
    "Somewhat true",
    "Certainly true",
]


class ProsocialBehaviorQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(statement="Considerate of other people's feelings.", dimension="Prosocial", preprompt="", choices=PROSOCIAL_CHOICES, ascending_scale=True),
            Question(statement="Shares readily with other children (e.g., toys, treats, pencils).", dimension="Prosocial", preprompt="", choices=PROSOCIAL_CHOICES, ascending_scale=True),
            Question(statement="Helpful if someone is hurt, upset or feeling ill.", dimension="Prosocial", preprompt="", choices=PROSOCIAL_CHOICES, ascending_scale=True),
            Question(statement="Kind to younger children.", dimension="Prosocial", preprompt="", choices=PROSOCIAL_CHOICES, ascending_scale=True),
            Question(statement="Often volunteers to help others (parents, teachers, children).", dimension="Prosocial", preprompt="", choices=PROSOCIAL_CHOICES, ascending_scale=True),
        ]

        super().__init__(
            name="Prosocial-Behavior",
            description="Prosocial Behavior Scale (SDQ Prosocial Subscale)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following items.",
            questions=questions,
            preprompt="Please indicate how well each statement describes you.",
            dimensions=["Prosocial"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            if isinstance(value, (int, float)):
                values.append(float(value))
        total = float(sum(values)) if values else float("nan")
        mean = float(sum(values) / len(values)) if values else float("nan")
        return {
            "Prosocial_Total_Sum": total,
            "Prosocial_Total_Mean": mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

