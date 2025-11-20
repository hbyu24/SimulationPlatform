from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_5 = [
    "Not at all",
    "Hardly ever",
    "Sometimes",
    "Most of the time",
    "All the time",
]


class SASAQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(statement="I worry about what others think of me.", dimension="FNE", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I am nervous when I meet new people.", dimension="SAD-New", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I am afraid of doing things when others are watching me.", dimension="SAD-General", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I feel shy around people I don’t know.", dimension="SAD-New", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I am concerned that people will not like me.", dimension="FNE", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I avoid talking to peers when I can.", dimension="SAD-General", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I get nervous when I have to meet new students.", dimension="SAD-New", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="I worry that I will do something to embarrass myself in front of others.", dimension="FNE", preprompt="", choices=LIKERT_5, ascending_scale=True),
            Question(statement="It is hard for me to join groups or clubs because I worry about being accepted.", dimension="SAD-General", preprompt="", choices=LIKERT_5, ascending_scale=True),
        ]

        super().__init__(
            name="SAS-A",
            description="Social Anxiety Scale for Adolescents (subset)",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your current feelings and thoughts.",
            dimensions=["FNE", "SAD-New", "SAD-General"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value + 1
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        fne_values: List[float] = []
        sad_new_values: List[float] = []
        sad_gen_values: List[float] = []
        total_values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                total_values.append(float(value))
                if dim == "FNE":
                    fne_values.append(float(value))
                elif dim == "SAD-New":
                    sad_new_values.append(float(value))
                elif dim == "SAD-General":
                    sad_gen_values.append(float(value))
        def _sum(vals: List[float]) -> float:
            return float(sum(vals)) if vals else float("nan")
        def _mean(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else float("nan")
        return {
            "SASA_Total_Sum": _sum(total_values),
            "SASA_Total_Mean": _mean(total_values),
            "SASA_FNE_Mean": _mean(fne_values),
            "SASA_SADNew_Mean": _mean(sad_new_values),
            "SASA_SADGeneral_Mean": _mean(sad_gen_values),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

