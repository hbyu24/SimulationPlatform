from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


SPIN_CHOICES = [
    "Not at all",
    "A little bit",
    "Somewhat",
    "Very much",
    "Extremely",
]


class SPINQuestionnaire(QuestionnaireBase):
    def __init__(self):
        statements = [
            "I am afraid of people in authority.",
            "I am bothered by blushing in front of people.",
            "Parties and social events scare me.",
            "I avoid talking to people I don’t know.",
            "Being criticized scares me a lot.",
            "I avoid activities in which I am the center of attention.",
            "Talking to strangers scares me.",
            "I avoid having to give speeches.",
            "I am afraid of doing things when people might be watching me.",
            "Being embarrassed or looking stupid are among my worst fears.",
            "I avoid speaking to anyone in authority.",
            "I am uncomfortable mixing with people I don’t know well.",
            "I am embarrassed to be seen eating or drinking by myself.",
            "I get anxious if someone observes me at work.",
            "I worry about embarrassing myself in front of others.",
            "I avoid disagreeing with people in authority.",
            "I often avoid speaking to groups of people.",
        ]
        questions: List[Question] = [
            Question(
                statement=s,
                dimension="Social Anxiety",
                preprompt="",
                choices=SPIN_CHOICES,
                ascending_scale=True,
            )
            for s in statements
        ]

        super().__init__(
            name="SPIN",
            description="Social Phobia Inventory",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your current feelings and thoughts.",
            dimensions=["Social Anxiety"],
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
            "SPIN_Total_Sum": total_sum,
            "SPIN_Total_Mean": total_mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None