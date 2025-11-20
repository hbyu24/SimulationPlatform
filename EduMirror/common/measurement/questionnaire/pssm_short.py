from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_5_PSSM = [
    "Not at all true",
    "Somewhat not true",
    "Neutral",
    "Somewhat true",
    "Completely true",
]


class PSSMShortQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="I feel like a real part of this school.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=True,
            ),
            Question(
                statement="People at this school notice when I’m good at something.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=True,
            ),
            Question(
                statement="Other students in this school take my opinions seriously.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=True,
            ),
            Question(
                statement="I feel proud to belong to this school.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=True,
            ),
            Question(
                statement="There’s at least one teacher or adult whom I can talk to if I have a problem at school.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=True,
            ),
            Question(
                statement="I feel respected at this school.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=True,
            ),
            Question(
                statement="Sometimes I feel as if I don’t belong at this school.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=False,
            ),
            Question(
                statement="Teachers at this school are interested in me.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=True,
            ),
            Question(
                statement="I feel accepted in this school.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=True,
            ),
            Question(
                statement="People here know I can do good work.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=True,
            ),
            Question(
                statement="I feel like I am not wanted at this school.",
                dimension="School Membership",
                preprompt="",
                choices=LIKERT_5_PSSM,
                ascending_scale=False,
            ),
        ]

        super().__init__(
            name="PSSM-Short",
            description="Psychological Sense of School Membership – Short Form",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following items.",
            questions=questions,
            preprompt="Please respond based on how true each statement is for you.",
            dimensions=["School Membership"],
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
            "PSSM_Total_Sum": total,
            "PSSM_Total_Mean": mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

