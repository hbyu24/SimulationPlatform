from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_5_GOSSIP = [
    "Strongly disagree",
    "Disagree",
    "Neither agree nor disagree",
    "Agree",
    "Strongly agree",
]


class GOSSIPQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="I often enjoy listening to gossip about other people.",
                dimension="Gossip Tendency",
                preprompt="",
                choices=LIKERT_5_GOSSIP,
                ascending_scale=True,
            ),
            Question(
                statement="I like to pass on information about others when I hear interesting things.",
                dimension="Gossip Tendency",
                preprompt="",
                choices=LIKERT_5_GOSSIP,
                ascending_scale=True,
            ),
            Question(
                statement="When friends share secrets with me, I feel excited to know something others don’t.",
                dimension="Gossip Tendency",
                preprompt="",
                choices=LIKERT_5_GOSSIP,
                ascending_scale=True,
            ),
            Question(
                statement="I sometimes feel left out when people gossip and I don’t know what they are talking about.",
                dimension="Gossip Tendency",
                preprompt="",
                choices=LIKERT_5_GOSSIP,
                ascending_scale=True,
            ),
            Question(
                statement="I tell interesting stories about other people to my friends.",
                dimension="Gossip Tendency",
                preprompt="",
                choices=LIKERT_5_GOSSIP,
                ascending_scale=True,
            ),
            Question(
                statement="I believe that talking about others can be useful for getting along with people.",
                dimension="Gossip Tendency",
                preprompt="",
                choices=LIKERT_5_GOSSIP,
                ascending_scale=True,
            ),
            Question(
                statement="I make an effort to keep up with the latest news about people I know.",
                dimension="Gossip Tendency",
                preprompt="",
                choices=LIKERT_5_GOSSIP,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="GOSSIP",
            description="Tendency to Gossip Questionnaire (Adapted)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your usual tendencies.",
            dimensions=["Gossip Tendency"],
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
        total = float(sum(values)) if values else float("nan")
        mean = float(sum(values) / len(values)) if values else float("nan")
        return {
            "GOSSIP_Total_Sum": total,
            "GOSSIP_Total_Mean": mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
