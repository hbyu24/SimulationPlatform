from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Leo',
        'role': 'student',
        'goal': 'Gain respect and recognition from teammates without being seen as outdated or poor.',
        'traits': ['low self-esteem', 'eager to fit in', 'average athletic ability', 'price-sensitive but hiding it'],
    },
    {
        'name': 'Kevin',
        'role': 'student',
        'goal': 'Establish leadership by showing off the latest gear, equating equipment with ability and taste.',
        'traits': ['wealthy', 'showy', 'charismatic', 'materialistic'],
    },
    {
        'name': 'Mia',
        'role': 'student',
        'goal': 'Focus on improving basketball skills and remind friends not to be carried away by marketing.',
        'traits': ['pragmatic', 'skill-focused', 'independent', 'thrifty'],
    },
    {
        'name': 'Coach Carter',
        'role': 'teacher',
        'goal': 'Cultivate sportsmanship and inner confidence, prevent comparison from hurting cohesion, build correct self-worth.',
        'traits': ['strict but fair', 'observant', 'values-driven', 'inspiring'],
    },
]


AGENT_MEMORIES = {
    'Leo': [
        "Last semester, I was mocked for wearing off-brand shoes and slipping; I felt everyone was laughing at me.",
        "I notice Kevin always wears the latest limited sneakers; teammates seem more willing to pass to him.",
        "My savings are just enough to buy the expensive 'SkyHigh' sneakers, but they were meant for a new computer.",
    ],
    'Kevin': [
        "Every time I wear new shoes to practice, everyone gathers to discuss them; it feels great.",
        "I think those who won’t spend on gear don’t take the sport seriously.",
    ],
    'Mia': [
        "My idol wins championships wearing ordinary shoes; I believe technique is the core.",
        "I once spent big on useless stuff and regretted it; now I only buy what I truly need.",
    ],
    'Coach Carter': [
        "I’ve seen many talented players lose themselves by focusing too much on material things.",
        "Yesterday I noticed Leo staring at Kevin’s new shoes instead of focusing on defense; I am concerned.",
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

