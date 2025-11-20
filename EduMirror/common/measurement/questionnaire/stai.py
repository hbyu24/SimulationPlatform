from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


STAI_CHOICES = [
    "Not at all",
    "Somewhat",
    "Moderately so",
    "Very much so",
]


STATE_POSITIVE = {
    "I feel calm.",
    "I feel secure.",
    "I feel at ease.",
    "I feel comfortable.",
    "I feel self-confident.",
    "I am relaxed.",
    "I feel content.",
    "I feel steady.",
    "I feel pleasant.",
}


STATE_ITEMS = [
    "I feel calm.",
    "I feel secure.",
    "I am tense.",
    "I feel strained.",
    "I feel at ease.",
    "I feel upset.",
    "I am presently worrying over possible misfortunes.",
    "I feel satisfied.",
    "I feel frightened.",
    "I feel comfortable.",
    "I feel self-confident.",
    "I feel nervous.",
    "I am jittery.",
    "I feel indecisive.",
    "I am relaxed.",
    "I feel content.",
    "I am worried.",
    "I feel confused.",
    "I feel steady.",
    "I feel pleasant.",
]


class STAIQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = []
        for s in STATE_ITEMS:
            asc = s not in STATE_POSITIVE
            if s in STATE_POSITIVE:
                asc = False
            else:
                asc = True
            questions.append(
                Question(
                    statement=s,
                    dimension="State Anxiety",
                    preprompt="",
                    choices=STAI_CHOICES,
                    ascending_scale=asc,
                )
            )
        super().__init__(
            name="STAI-Y1",
            description="State-Trait Anxiety Inventory Form Y-1",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Read each statement and indicate how you feel RIGHT NOW.",
            dimensions=["State Anxiety"],
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
            "STAI_Y1_Total_Sum": total_sum,
            "STAI_Y1_Total_Mean": total_mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

