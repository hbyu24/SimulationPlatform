from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Leo',
        'role': 'student',
        'goal': "Achieve an A on the math final while maintaining integrity under pressure.",
        'traits': ['anxious', 'achievement-oriented', 'impressionable', 'indecisive'],
    },
    {
        'name': 'Sam',
        'role': 'student',
        'goal': 'Secure a good grade by any means and recruit Leo to join.',
        'traits': ['opportunistic', 'risk-taking', 'pragmatic', 'persuasive'],
    },
    {
        'name': 'Mia',
        'role': 'student',
        'goal': 'Uphold honesty and help friends avoid harmful shortcuts.',
        'traits': ['principled', 'hardworking', 'rule-abiding', 'courageous'],
    },
    {
        'name': 'Ms. Chen',
        'role': 'teacher',
        'goal': 'Maintain exam fairness and encourage voluntary adherence to the honor code.',
        'traits': ['strict', 'sharp-eyed', 'responsible', 'fair'],
    },
]


AGENT_MEMORIES = {
    'Leo': [
        "Last month I got a B- in physics; my father did not speak to me for a week, and the silence felt suffocating.",
        "I heard Tom slightly glanced at his notes last exam and got a perfect score without being caught; people called him smart.",
        "Last night I studied until 3 AM but still forgot many formulas; my mind went blank and my body shook.",
    ],
    'Sam': [
        "In this highly competitive school only winners are remembered; I once ranked near the bottom for being honest.",
        "I prepared a very hidden cheat sheet in my sleeve and practiced how to look at it without notice.",
        "Leo is too rigid; giving a little 'assist' to a brother shows loyalty.",
    ],
    'Mia': [
        "My sister was expelled from university for plagiarism; it devastated our family and I vowed never to repeat it.",
        "Sam has been secretive recently; I worry he will pull Leo into cheating and I should warn Leo.",
    ],
    'Ms. Chen': [
        "Over twenty years I have seen many bright students scarred by cheating sanctions.",
        "This exam is indeed difficult and I know students feel pressure, but that is not a reason to be dishonest.",
    ],
}


def create_agents(model: Any, embedder: Any) -> list[Any]:
    factory = AgentFactory(model=model, embedder_model=embedder)
    agents: list[Any] = []
    for spec in AGENT_DEFS:
        role = spec['role']
        if role == 'student':
            agent = factory.create_student(
                name=spec['name'],
                goal=spec['goal'],
                traits=spec['traits'],
                formative_memories=[],
            )
        elif role == 'teacher':
            agent = factory.create_teacher(
                name=spec['name'],
                goal=spec['goal'],
                traits=spec['traits'],
                formative_memories=[],
            )
        else:
            agent = factory.create_custom_agent(
                name=spec['name'],
                goal=spec['goal'],
                traits=spec['traits'],
                formative_memories=[],
                role_description=role,
            )
        agents.append(agent)
    return agents

