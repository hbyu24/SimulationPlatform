from typing import Any, Dict, List, Optional, Tuple

from concordia.contrib.data.questionnaires.base_questionnaire import (
    QuestionnaireBase,
    Question,
)


LIKERT_5_SRASR = [
    "Never",
    "Seldom",
    "Sometimes",
    "Often",
    "Always",
]


class SRASRQuestionnaire(QuestionnaireBase):
    def __init__(self):
        questions: List[Question] = [
            Question(
                statement="I get scared or upset in school.",
                dimension="Negative Affect",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="I get nervous when I go to school.",
                dimension="Negative Affect",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="I feel bad at school because I worry about something bad happening.",
                dimension="Negative Affect",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="I would rather not go to school because my classmates or teachers may think I’m not smart enough.",
                dimension="Social/Evaluative",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="Going to school makes me feel nervous about being called on in class or having to give a speech.",
                dimension="Social/Evaluative",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="I would rather not go to school if I might get embarrassed in front of my classmates.",
                dimension="Social/Evaluative",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="I want to stay home from school because I want to be with my mom or dad.",
                dimension="Attention",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="I want to stay home from school to spend time with people important to me.",
                dimension="Attention",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="I want to stay home so that someone will pay more attention to me.",
                dimension="Attention",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="I would rather do fun things outside school instead of going to school.",
                dimension="Tangible Reinforcement",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="I try to miss school so I can do things I like better than school.",
                dimension="Tangible Reinforcement",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
            Question(
                statement="I want to skip school to do fun activities.",
                dimension="Tangible Reinforcement",
                preprompt="",
                choices=LIKERT_5_SRASR,
                ascending_scale=True,
            ),
        ]

        super().__init__(
            name="SRAS-R",
            description="School Refusal Assessment Scale - Revised",
            questionnaire_type="multiple_choice",
            observation_preprompt="You are participating in an in-situ interview. Answer the following scale items.",
            questions=questions,
            preprompt="Please respond based on your current feelings and reasons regarding school attendance.",
            dimensions=["Negative Affect", "Social/Evaluative", "Attention", "Tangible Reinforcement"],
        )

    def process_answer(self, player_name: str, answer_text: str, question: Question) -> Tuple[str, Any]:
        dim, base_value = super().process_answer(player_name, answer_text, question)
        if isinstance(base_value, int):
            return dim, base_value
        return dim, None

    def aggregate_results(self, player_answers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        sums: Dict[str, float] = {
            "Negative Affect": 0.0,
            "Social/Evaluative": 0.0,
            "Attention": 0.0,
            "Tangible Reinforcement": 0.0,
        }
        counts: Dict[str, int] = {k: 0 for k in sums.keys()}
        for _, qdata in player_answers.items():
            dim = qdata.get("dimension")
            value = qdata.get("value")
            if isinstance(dim, str) and isinstance(value, (int, float)) and dim in sums:
                sums[dim] += float(value)
                counts[dim] += 1
        return {
            "SRASR_NegativeAffect": float(sums["Negative Affect"]) if counts["Negative Affect"] > 0 else float("nan"),
            "SRASR_SocialEvaluative": float(sums["Social/Evaluative"]) if counts["Social/Evaluative"] > 0 else float("nan"),
            "SRASR_Attention": float(sums["Attention"]) if counts["Attention"] > 0 else float("nan"),
            "SRASR_TangibleReinforcement": float(sums["Tangible Reinforcement"]) if counts["Tangible Reinforcement"] > 0 else float("nan"),
        }

    def plot_results(
        self,
        results_df,
        label_column: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        return None

