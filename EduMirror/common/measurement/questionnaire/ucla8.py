from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_4 = [
    "Never",
    "Rarely",
    "Sometimes",
    "Often",
]


class UCLA8Questionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="That you are in tune with the people around you?",
                dimension="UCLA Loneliness",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=False,
            ),
            Question(
                statement="That you lack companionship?",
                dimension="UCLA Loneliness",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
            Question(
                statement="That there is no one you can turn to?",
                dimension="UCLA Loneliness",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
            Question(
                statement="That you are an outgoing, sociable person?",
                dimension="UCLA Loneliness",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=False,
            ),
            Question(
                statement="That you feel alone?",
                dimension="UCLA Loneliness",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
            Question(
                statement="That you feel part of a group of friends?",
                dimension="UCLA Loneliness",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=False,
            ),
            Question(
                statement="That you have a lot in common with the people around you?",
                dimension="UCLA Loneliness",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=False,
            ),
            Question(
                statement="That you are no longer close to anyone?",
                dimension="UCLA Loneliness",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="UCLA-8",
            description="UCLA Loneliness Scale - Short Form (8 items)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your feelings in general.",
            dimensions=["UCLA Loneliness"],
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
        total = float(sum(values)) if values else float("nan")
        mean = float(sum(values) / len(values)) if values else float("nan")
        return {
            "UCLA8_Total_Sum": total,
            "UCLA8_Total_Mean": mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
