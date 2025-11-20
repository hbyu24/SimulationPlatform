from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


GMS_CHOICES = [
    "Strongly disagree",
    "Disagree",
    "Agree",
    "Strongly agree",
]


ITEMS = [
    ("You have a certain amount of intelligence, and you really can’t do much to change it.", False),
    ("Your intelligence is something about you that you can’t change very much.", False),
    ("You can learn new things, but you can’t really change your basic intelligence.", False),
    ("No matter who you are, you can change your intelligence a lot.", True),
    ("You can always substantially change how intelligent you are.", True),
    ("You can get much better at the things you try, no matter how hard they are at first.", True),
]


class GMSQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = []
        for s, growth in ITEMS:
            questions.append(
                Question(
                    statement=s,
                    dimension="Growth Mindset",
                    preprompt="",
                    choices=GMS_CHOICES,
                    ascending_scale=True if growth else False,
                )
            )
        super().__init__(
            name="GMS",
            description="Growth Mindset Scale",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please indicate how much you agree or disagree.",
            dimensions=["Growth Mindset"],
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
            "GMS_Total_Sum": total_sum,
            "GMS_Total_Mean": total_mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

