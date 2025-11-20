from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


GEDS_CHOICES = [
    "Never",
    "Once",
    "2-3 times",
    "4 or more times",
]


class GEDSQuestionnaireBrief(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="You were treated unfairly because of your ethnicity.",
                dimension="Perceived Discrimination",
                preprompt="",
                choices=GEDS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="You were called names or insulted because of your ethnicity.",
                dimension="Perceived Discrimination",
                preprompt="",
                choices=GEDS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="People acted as if they were afraid of you because of your ethnicity.",
                dimension="Perceived Discrimination",
                preprompt="",
                choices=GEDS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="You were kept out of social groups or clubs because of your ethnicity.",
                dimension="Perceived Discrimination",
                preprompt="",
                choices=GEDS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="You were followed around in stores because of your ethnicity.",
                dimension="Perceived Discrimination",
                preprompt="",
                choices=GEDS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="Other students/people made fun of your ethnicity.",
                dimension="Perceived Discrimination",
                preprompt="",
                choices=GEDS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="You were ignored or excluded because of your ethnicity.",
                dimension="Perceived Discrimination",
                preprompt="",
                choices=GEDS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="People acted as if they thought you were not smart because of your ethnicity.",
                dimension="Perceived Discrimination",
                preprompt="",
                choices=GEDS_CHOICES,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="GEDS_Brief",
            description="General Ethnic Discrimination Scale – Brief Version",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your recent experiences.",
            dimensions=["Perceived Discrimination"],
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
            "GEDS_Total_Sum": total_sum,
            "GEDS_Total_Mean": total_mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

