from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Leo',
        'role': 'student',
        'goal': 'Join the Comic Club to pursue true passion while keeping family harmony.',
        'traits': ['creative', 'introverted', 'compliant-yet-opinionated', 'conflict-sensitive'],
    },
    {
        'name': 'Margaret',
        'role': 'parent',
        'goal': 'Ensure Leo gains practical skills and chooses the coding boot camp for future competitiveness.',
        'traits': ['pragmatic', 'anxious', 'protective', 'goal-oriented'],
    },
    {
        'name': 'Ms. Chen',
        'role': 'teacher',
        'goal': 'Support Leo’s artistic pursuit and help parents understand autonomy’s long-term value.',
        'traits': ['supportive', 'observant', 'good-listener', 'autonomy-supportive'],
    },
]


AGENT_MEMORIES = {
    'Leo': [
        "Last month my art piece was selected for a school exhibition; I felt strong competence and pride.",
        "Last summer I was forced into an olympiad math class; I felt anxious and bored and the outcome was poor.",
        "Last night I overheard Mom saying without STEM skills the future is hopeless; I felt scared to speak up.",
    ],
    'Margaret': [
        "A coworker was laid off recently due to limited skill set; it reinforced my focus on practical skills.",
        "Leo has been gentle since childhood; I worry he will choose poorly without my guidance.",
        "Media reports emphasize STEM education; I believe coding is essential while comics waste time.",
    ],
    'Ms. Chen': [
        "I have seen students become disengaged and depressed when forced to abandon their passions.",
        "Last week at club preview Leo stared at the poster with rare spark in his eyes.",
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
        elif role == 'parent':
            agent = factory.create_parent(
                name=spec['name'],
                goal=spec['goal'],
                traits=spec['traits'],
                formative_memories=[],
                child_name='Leo',
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
