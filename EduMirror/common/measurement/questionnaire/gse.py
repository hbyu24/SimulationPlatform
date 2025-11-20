from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


GSE_CHOICES = [
    "Not at all true",
    "Hardly true",
    "Moderately true",
    "Exactly true",
]


GSE_ITEMS = [
    "I can always manage to solve difficult problems if I try hard enough.",
    "If someone opposes me, I can find the means and ways to get what I want.",
    "It is easy for me to stick to my aims and accomplish my goals.",
    "I am confident that I could deal efficiently with unexpected events.",
    "Thanks to my resourcefulness, I know how to handle unforeseen situations.",
    "I can solve most problems if I invest the necessary effort.",
    "I can remain calm when facing difficulties because I can rely on my coping abilities.",
    "When I am confronted with a problem, I can usually find several solutions.",
    "If I am in trouble, I can usually think of a solution.",
    "I can usually handle whatever comes my way.",
]


class GSEQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement=s,
                dimension="General Self-Efficacy",
                preprompt="",
                choices=GSE_CHOICES,
                ascending_scale=True,
            )
            for s in GSE_ITEMS
        ]
        super().__init__(
            name="GSE",
            description="General Self-Efficacy Scale",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please indicate how true each statement is for you.",
            dimensions=["General Self-Efficacy"],
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
            "GSE_Total_Sum": total_sum,
            "GSE_Total_Mean": total_mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
