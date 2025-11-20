from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)

LIKERT_5_FSPS = [
    "Strongly Disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly Agree",
]

class FSPSQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = []
        questions.extend([
            Question(
                statement="I trust the teachers at this school to act in my child’s best interest.",
                dimension="Trust",
                preprompt="",
                choices=LIKERT_5_FSPS,
                ascending_scale=True,
            ),
            Question(
                statement="I feel comfortable sharing my concerns with school staff.",
                dimension="Trust",
                preprompt="",
                choices=LIKERT_5_FSPS,
                ascending_scale=True,
            ),
            Question(
                statement="I believe that the school is open and honest in their communications with me.",
                dimension="Trust",
                preprompt="",
                choices=LIKERT_5_FSPS,
                ascending_scale=True,
            ),
            Question(
                statement="The school follows through on what they say they will do.",
                dimension="Trust",
                preprompt="",
                choices=LIKERT_5_FSPS,
                ascending_scale=True,
            ),
            Question(
                statement="I feel my input is respected and valued by the school.",
                dimension="Trust",
                preprompt="",
                choices=LIKERT_5_FSPS,
                ascending_scale=True,
            ),
        ])
        questions.extend([
            Question(
                statement="The school keeps me well informed about my child’s progress.",
                dimension="Communication",
                preprompt="",
                choices=LIKERT_5_FSPS,
                ascending_scale=True,
            ),
            Question(
                statement="Teachers and staff at this school communicate with me regularly.",
                dimension="Communication",
                preprompt="",
                choices=LIKERT_5_FSPS,
                ascending_scale=True,
            ),
            Question(
                statement="I am encouraged to ask questions and provide feedback.",
                dimension="Communication",
                preprompt="",
                choices=LIKERT_5_FSPS,
                ascending_scale=True,
            ),
            Question(
                statement="The school makes it easy for me to contact teachers or staff when needed.",
                dimension="Communication",
                preprompt="",
                choices=LIKERT_5_FSPS,
                ascending_scale=True,
            ),
            Question(
                statement="Responses to my inquiries are timely and helpful.",
                dimension="Communication",
                preprompt="",
                choices=LIKERT_5_FSPS,
                ascending_scale=True,
            ),
        ])

        super().__init__(
            name="FSPS",
            description="Family-School Partnership Scale – Trust and Communication",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following items.",
            questions=questions,
            preprompt="Please rate each statement about your relationship with the school.",
            dimensions=["Trust", "Communication"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        trust_values: List[float] = []
        comm_values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)) and isinstance(dim, str):
                if dim == "Trust":
                    trust_values.append(float(value))
                elif dim == "Communication":
                    comm_values.append(float(value))
        trust_total = float(sum(trust_values)) if trust_values else float("nan")
        trust_mean = float(sum(trust_values) / len(trust_values)) if trust_values else float("nan")
        comm_total = float(sum(comm_values)) if comm_values else float("nan")
        comm_mean = float(sum(comm_values) / len(comm_values)) if comm_values else float("nan")
        all_values = trust_values + comm_values
        total = float(sum(all_values)) if all_values else float("nan")
        mean = float(sum(all_values) / len(all_values)) if all_values else float("nan")
        return {
            "FSPS_Trust_Sum": trust_total,
            "FSPS_Trust_Mean": trust_mean,
            "FSPS_Communication_Sum": comm_total,
            "FSPS_Communication_Mean": comm_mean,
            "FSPS_Total_Sum": total,
            "FSPS_Total_Mean": mean,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None
