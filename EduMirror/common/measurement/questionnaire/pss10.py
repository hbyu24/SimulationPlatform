from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_5_PSS = [
    "Never",
    "Almost Never",
    "Sometimes",
    "Fairly Often",
    "Very Often",
]


class PSS10Questionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="In the last month, how often have you been upset because of something that happened unexpectedly?",
                dimension="Perceived Stress",
                preprompt="",
                choices=LIKERT_5_PSS,
                ascending_scale=True,
            ),
            Question(
                statement="In the last month, how often have you felt that you were unable to control the important things in your life?",
                dimension="Perceived Stress",
                preprompt="",
                choices=LIKERT_5_PSS,
                ascending_scale=True,
            ),
            Question(
                statement="In the last month, how often have you felt nervous and stressed?",
                dimension="Perceived Stress",
                preprompt="",
                choices=LIKERT_5_PSS,
                ascending_scale=True,
            ),
            Question(
                statement="In the last month, how often have you felt confident about your ability to handle your personal problems?",
                dimension="Perceived Stress",
                preprompt="",
                choices=LIKERT_5_PSS,
                ascending_scale=False,
            ),
            Question(
                statement="In the last month, how often have you felt that things were going your way?",
                dimension="Perceived Stress",
                preprompt="",
                choices=LIKERT_5_PSS,
                ascending_scale=False,
            ),
            Question(
                statement="In the last month, how often have you found that you could not cope with all the things that you had to do?",
                dimension="Perceived Stress",
                preprompt="",
                choices=LIKERT_5_PSS,
                ascending_scale=True,
            ),
            Question(
                statement="In the last month, how often have you been able to control irritations in your life?",
                dimension="Perceived Stress",
                preprompt="",
                choices=LIKERT_5_PSS,
                ascending_scale=False,
            ),
            Question(
                statement="In the last month, how often have you felt that you were on top of things?",
                dimension="Perceived Stress",
                preprompt="",
                choices=LIKERT_5_PSS,
                ascending_scale=False,
            ),
            Question(
                statement="In the last month, how often have you been angered because of things that were outside of your control?",
                dimension="Perceived Stress",
                preprompt="",
                choices=LIKERT_5_PSS,
                ascending_scale=True,
            ),
            Question(
                statement="In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?",
                dimension="Perceived Stress",
                preprompt="",
                choices=LIKERT_5_PSS,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="PSS-10",
            description="Perceived Stress Scale - 10 items",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your experiences in the last month.",
            dimensions=["Perceived Stress"],
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
            "PSS10_Total_Sum": total,
            "PSS10_Total_Mean": mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
