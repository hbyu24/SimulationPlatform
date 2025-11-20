from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Alex',
        'role': 'student',
        'goal': 'Gain acceptance while coping with material comparison pressure.',
        'traits': ['insecure', 'materialistic', 'envious', 'eager to fit in'],
    },
    {
        'name': 'Ben',
        'role': 'student',
        'goal': 'Maintain friendships with a balanced view of material possessions.',
        'traits': ['rational', 'independent', 'observant'],
    },
    {
        'name': 'Chloe',
        'role': 'student',
        'goal': 'Show off new expensive items and enjoy superiority.',
        'traits': ['showy', 'narcissistic', 'unsympathetic', 'popular'],
    },
    {
        'name': 'Jordan',
        'role': 'parent',
        'goal': 'Teach true value of money and avoid vanity habits.',
        'traits': ['pragmatic', 'frugal', 'traditional', 'principled'],
    },
    {
        'name': 'Mrs. Lee',
        'role': 'teacher',
        'goal': 'Detect unhealthy comparison and guide confidence based on inner qualities.',
        'traits': ['perceptive', 'caring', 'guiding'],
    },
]


AGENT_MEMORIES = {
    'Alex': [
        "Last term I felt small when peers whispered about my outdated sneakers.",
        "I always follow what Chloe owns; each time she shows a new item, I feel painful envy.",
        "My parents say money should be used wisely; I feel inferior compared to others.",
    ],
    'Ben': [
        "I think items do not define coolness; friendship is not about possessions.",
        "I noticed Alex gets upset when others show off expensive items.",
    ],
    'Chloe': [
        "My parents reward me with the latest gifts for good grades.",
        "In this class, latest tech equals voice and status.",
    ],
    'Jordan': [
        "Our savings are for college and emergencies, not chasing trends.",
        "Alex increasingly asks for expensive items; I worry about his values.",
    ],
    'Mrs. Lee': [
        "I observed unhealthy comparison in class and want to guide a healthier value system.",
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
                child_name='Alex',
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

