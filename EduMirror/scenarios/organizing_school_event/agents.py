from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Mrs. Lee',
        'role': 'teacher',
        'goal': 'Ensure smooth charity fair, raise funds, and maintain positive parent relations.',
        'traits': ['conscientious', 'anxious', 'consensus-seeking', 'professional'],
    },
    {
        'name': 'Mrs. Chen',
        'role': 'parent',
        'goal': 'Demonstrate organizational ability and make our class stall the best.',
        'traits': ['enthusiastic', 'domineering', 'high-standard', 'outspoken'],
    },
    {
        'name': 'Mr. Wang',
        'role': 'parent',
        'goal': 'Support financially with minimal time commitment; resolve issues efficiently.',
        'traits': ['pragmatic', 'busy', 'conflict-avoidant', 'generous'],
    },
    {
        'name': 'Lily',
        'role': 'student',
        'goal': 'Hope parents cooperate without arguing for a joyful charity event.',
        'traits': ['observant', 'eager-to-please', 'caught-in-between'],
    },
]


AGENT_MEMORIES = {
    'Mrs. Lee': [
        "Last year a parent disagreement caused chaos at an event; I was criticized by the grade leader and now feel anxious about large-event coordination.",
        "I know Mr. Wang has resources but is busy, while Mrs. Chen is passionate but controlling; balancing them is my biggest challenge.",
    ],
    'Mrs. Chen': [
        "I worked as a project manager and cannot stand inefficiency and poor planning; when things look messy I step in.",
        "I feel it is unfair when others (especially Mr. Wang) contribute money but not effort; I want more commitment from them.",
    ],
    'Mr. Wang': [
        "My work is in a critical phase and I handle emails every minute; financial support is also participation and is often misunderstood.",
        "I feel uncomfortable with Mrs. Chen’s aggressive attitude; I tend to stay silent or donate to avoid arguments.",
    ],
    'Lily': [
        "I wish parents would cooperate happily without arguing so our charity fair is joyful.",
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
                child_name='Lily',
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

