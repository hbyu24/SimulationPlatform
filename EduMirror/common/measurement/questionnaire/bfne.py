from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


BFNE_CHOICES = [
    "Not at all characteristic of me",
    "Slightly characteristic of me",
    "Moderately characteristic of me",
    "Very characteristic of me",
    "Extremely characteristic of me",
]


class BFNEQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="I worry about what other people will think of me.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I am afraid that others will not approve of me.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I am afraid that people will find fault with me.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I am concerned about what other people think of me.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I am worried that people will think negatively of me.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I am afraid others will turn away from me.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I am afraid people will not like me.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I am often worried that people will notice my shortcomings.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I rarely worry about what kind of impression I am making on someone.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I am not afraid of being evaluated negatively.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I am not concerned with what others think of me.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=False,
            ),
            Question(
                statement="I am not afraid that others will find fault with me.",
                dimension="Fear of Negative Evaluation",
                preprompt="",
                choices=BFNE_CHOICES,
                ascending_scale=False,
            ),
        ]

        super().__init__(
            name="BFNE",
            description="Brief Fear of Negative Evaluation Scale",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your current feelings and thoughts.",
            dimensions=["Fear of Negative Evaluation"],
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
            "BFNE_Total_Sum": total_sum,
            "BFNE_Total_Mean": total_mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
