from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


RSQ_CONCERN_CHOICES = [
    "Not at all anxious/worried",
    "Slightly anxious/worried",
    "Moderately anxious/worried",
    "Quite anxious/worried",
    "Very anxious/worried",
]

RSQ_EXPECTATION_CHOICES = [
    "Very unlikely to be rejected",
    "Unlikely to be rejected",
    "Neutral",
    "Likely to be rejected",
    "Very likely to be rejected",
]


class RSQQuestionnaire(QuestionnaireBase):
    def __init__(self):
        scenarios = [
            "You ask a classmate if you can join in a game they are playing.",
            "You ask a friend to do homework together.",
            "You ask your parent if you can go to a party.",
            "You ask a group of kids if you can eat lunch with them.",
            "You ask your teacher for extra help with an assignment after class.",
            "You call a friend to invite them over.",
            "You ask a friend to share something with you.",
            "You invite a classmate to your birthday party.",
        ]
        questions: List[Question] = []
        for idx, s in enumerate(scenarios, start=1):
            questions.append(
                Question(
                    statement=f"RSQ Scenario {idx} - Concern: {s}",
                    dimension="RSQ_Concern",
                    preprompt="",
                    choices=RSQ_CONCERN_CHOICES,
                    ascending_scale=True,
                )
            )
            questions.append(
                Question(
                    statement=f"RSQ Scenario {idx} - Expectation: {s}",
                    dimension="RSQ_Expectation",
                    preprompt="",
                    choices=RSQ_EXPECTATION_CHOICES,
                    ascending_scale=True,
                )
            )

        super().__init__(
            name="RS-Q",
            description="Rejection Sensitivity Questionnaire (Children/Adolescent version)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following items.",
            questions=questions,
            preprompt="Please imagine yourself in each situation and respond.",
            dimensions=["RSQ_Concern", "RSQ_Expectation"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        return super().process_answer(player_name, answer_text, question)

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        concern_vals: List[float] = []
        expect_vals: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                if dim == "RSQ_Concern":
                    concern_vals.append(float(value))
                elif dim == "RSQ_Expectation":
                    expect_vals.append(float(value))
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        cm = _mean(concern_vals)
        em = _mean(expect_vals)
        return {
            "RSQ_Concern_Mean": cm,
            "RSQ_Expectation_Mean": em,
            "RSQ_Composite": float(cm * em) if cm == cm and em == em else float("nan"),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
