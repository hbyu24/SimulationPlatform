from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_4_DASS = [
    "Did not apply to me at all",
    "Applied to me to some degree, or some of the time",
    "Applied to me to a considerable degree, or a good part of time",
    "Applied to me very much, or most of the time",
]


class DASS21Questionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="I couldn't seem to experience any positive feeling at all.",
                dimension="Depression",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I found it difficult to work up the initiative to do things.",
                dimension="Depression",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I felt that I had nothing to look forward to.",
                dimension="Depression",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I felt down-hearted and blue.",
                dimension="Depression",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I was unable to become enthusiastic about anything.",
                dimension="Depression",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I felt I wasn't worth much as a person.",
                dimension="Depression",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I felt that life was meaningless.",
                dimension="Depression",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I experienced breathing difficulty (e.g., overly rapid breathing, breathlessness in the absence of physical exertion).",
                dimension="Anxiety",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I found it hard to wind down.",
                dimension="Anxiety",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I tended to over-react to situations.",
                dimension="Anxiety",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I experienced trembling (e.g., in the hands).",
                dimension="Anxiety",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I felt I was close to panic.",
                dimension="Anxiety",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I was aware of dryness of my mouth.",
                dimension="Anxiety",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I experienced difficulty swallowing.",
                dimension="Anxiety",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I found it difficult to relax.",
                dimension="Stress",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I was intolerant of anything that kept me from getting on with what I was doing.",
                dimension="Stress",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I felt that I was rather touchy.",
                dimension="Stress",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I was unable to become enthusiastic about anything.",
                dimension="Stress",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I found myself getting agitated.",
                dimension="Stress",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I found it hard to calm down after something upset me.",
                dimension="Stress",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
            Question(
                statement="I felt that I was using a lot of nervous energy.",
                dimension="Stress",
                preprompt="",
                choices=LIKERT_4_DASS,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="DASS-21",
            description="Depression Anxiety Stress Scales - 21 items",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your experiences over the past week.",
            dimensions=["Depression", "Anxiety", "Stress"],
        )

    def process_answer(self, player_name: str, answer_text: str, question: Question) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        sums: Dict[str, float] = {"Depression": 0.0, "Anxiety": 0.0, "Stress": 0.0}
        counts: Dict[str, int] = {"Depression": 0, "Anxiety": 0, "Stress": 0}
        for _, qdata in player_answers.items():
            dim = qdata.get("dimension")
            value = qdata.get("value")
            if isinstance(dim, str) and isinstance(value, (int, float)) and dim in sums:
                sums[dim] += float(value)
                counts[dim] += 1
        dep = float(sums["Depression"]) * 2 if counts["Depression"] > 0 else float("nan")
        anx = float(sums["Anxiety"]) * 2 if counts["Anxiety"] > 0 else float("nan")
        strv = float(sums["Stress"]) * 2 if counts["Stress"] > 0 else float("nan")
        return {
            "DASS21_Depression": dep,
            "DASS21_Anxiety": anx,
            "DASS21_Stress": strv,
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

