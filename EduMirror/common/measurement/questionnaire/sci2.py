from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_4 = [
    "Not at all",
    "Somewhat",
    "Mostly",
    "Completely",
]


class Sci2Questionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="I can trust people in this community.",
                dimension="Membership",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
            Question(
                statement="I feel like a member of this community.",
                dimension="Membership",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
            Question(
                statement="I have a say about what goes on in my community.",
                dimension="Influence",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
            Question(
                statement="People in this community listen to what I have to say.",
                dimension="Influence",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
            Question(
                statement="This community helps me fulfill my needs.",
                dimension="NeedsFulfillment",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
            Question(
                statement="I get important needs of mine met because I am part of this community.",
                dimension="NeedsFulfillment",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
            Question(
                statement="I have good bonds with others in this community.",
                dimension="EmotionalConnection",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
            Question(
                statement="I feel emotionally connected to others in this community.",
                dimension="EmotionalConnection",
                preprompt="",
                choices=LIKERT_4,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="SCI-2",
            description="Sense of Community Index-2",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please indicate how true each statement is for you.",
            dimensions=["Membership", "Influence", "NeedsFulfillment", "EmotionalConnection"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        dims = {
            "Membership": [],
            "Influence": [],
            "NeedsFulfillment": [],
            "EmotionalConnection": [],
        }
        total_values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                total_values.append(float(value))
                if dim in dims:
                    dims[dim].append(float(value))

        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")

        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")

        out: Dict[str, Any] = {
            "SCI2_Total_Sum": _sum(total_values),
            "SCI2_Total_Mean": _mean(total_values),
        }
        for k, vals in dims.items():
            out[f"SCI2_{k}_Sum"] = _sum(vals)
            out[f"SCI2_{k}_Mean"] = _mean(vals)
        return out

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

