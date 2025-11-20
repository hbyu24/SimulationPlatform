from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_5 = [
    "Strongly disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly agree",
]


class CesQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="Our group can achieve the goals we set for ourselves.",
                dimension="CollectiveEfficacy",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="We work together effectively to solve problems.",
                dimension="CollectiveEfficacy",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="We are confident in our ability to organize tasks as a team.",
                dimension="CollectiveEfficacy",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="As a team, we can overcome unexpected difficulties.",
                dimension="CollectiveEfficacy",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="We can successfully accomplish our group’s objectives.",
                dimension="CollectiveEfficacy",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="Our team can motivate each other to give our best effort.",
                dimension="CollectiveEfficacy",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="Our group can handle whatever comes our way.",
                dimension="CollectiveEfficacy",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
            Question(
                statement="We are able to coordinate and carry out activities as a team.",
                dimension="CollectiveEfficacy",
                preprompt="",
                choices=LIKERT_5,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="CES",
            description="Collective Efficacy Scale – Short Form",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Indicate how much you agree with each statement about your group.",
            dimensions=["CollectiveEfficacy"],
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

        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")

        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")

        return {
            "CES_Total_Sum": _sum(values),
            "CES_Total_Mean": _mean(values),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

