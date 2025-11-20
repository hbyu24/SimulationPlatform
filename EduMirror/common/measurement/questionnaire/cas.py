from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


CAS_CHOICES = [
    "Strongly Disagree",
    "Disagree",
    "Neither agree nor disagree",
    "Agree",
    "Strongly Agree",
]


class CASQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="My friends and I like to discuss what my favorite celebrity has done.",
                dimension="Entertainment-social",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I like to talk with others who admire my favorite celebrity.",
                dimension="Entertainment-social",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I enjoy watching, reading, or listening to my favorite celebrity.",
                dimension="Entertainment-social",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="Learning the life story of my favorite celebrity is a lot of fun to me.",
                dimension="Entertainment-social",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I enjoy hearing the insights of my favorite celebrity.",
                dimension="Entertainment-social",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I share with my favorite celebrity a special bond.",
                dimension="Intense-personal",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I have frequent thoughts about my favorite celebrity, even when I don’t want to.",
                dimension="Intense-personal",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="My favorite celebrity is my soul mate.",
                dimension="Intense-personal",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I have pictures and souvenirs of my favorite celebrity.",
                dimension="Intense-personal",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I feel compelled to learn the personal habits of my favorite celebrity.",
                dimension="Intense-personal",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I consider my favorite celebrity to be a friend.",
                dimension="Intense-personal",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="If I were lucky enough to meet my favorite celebrity, and he/she asked me to do something illegal as a favor, I would probably do it.",
                dimension="Borderline-pathological",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I would gladly die in order to save the life of my favorite celebrity.",
                dimension="Borderline-pathological",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="When something bad happens to my favorite celebrity I feel like it happened to me.",
                dimension="Borderline-pathological",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I would spend a lot of money to buy a personal item once owned by my favorite celebrity.",
                dimension="Borderline-pathological",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I often feel compelled to learn personal details about my favorite celebrity’s life.",
                dimension="Borderline-pathological",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I love to talk with others who admire my favorite celebrity.",
                dimension="Entertainment-social",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="Sometimes, I think my favorite celebrity is communicating with me in mysterious ways.",
                dimension="Borderline-pathological",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
            Question(
                statement="I would do anything for my favorite celebrity.",
                dimension="Borderline-pathological",
                preprompt="",
                choices=CAS_CHOICES,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="CAS",
            description="Celebrity Attitude Scale",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following items.",
            questions=questions,
            preprompt="Please respond based on your current feelings and thoughts.",
            dimensions=["Entertainment-social", "Intense-personal", "Borderline-pathological"],
        )

    def process_answer(
        self, player_name: str, answer_text: str, question: Question
    ) -> Tuple[str, Any]:
        return super().process_answer(player_name, answer_text, question)

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        total_values: List[float] = []
        ent_values: List[float] = []
        int_values: List[float] = []
        path_values: List[float] = []
        for _, qdata in player_answers.items():
            value = qdata.get("value")
            dim = qdata.get("dimension")
            if isinstance(value, (int, float)):
                v = float(value)
                total_values.append(v)
                if dim == "Entertainment-social":
                    ent_values.append(v)
                elif dim == "Intense-personal":
                    int_values.append(v)
                elif dim == "Borderline-pathological":
                    path_values.append(v)
        def _sum(xs: List[float]) -> float:
            return float(sum(xs)) if xs else float("nan")
        def _mean(xs: List[float]) -> float:
            return float(sum(xs) / len(xs)) if xs else float("nan")
        return {
            "CAS_Total_Sum": _sum(total_values),
            "CAS_Total_Mean": _mean(total_values),
            "CAS_Entertainment_Sum": _sum(ent_values),
            "CAS_Entertainment_Mean": _mean(ent_values),
            "CAS_Intense_Sum": _sum(int_values),
            "CAS_Intense_Mean": _mean(int_values),
            "CAS_Pathological_Sum": _sum(path_values),
            "CAS_Pathological_Mean": _mean(path_values),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

