from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Lily',
        'role': 'student',
        'goal': 'Find friends who understand my artistic interests and build deep connections while avoiding rejection or isolation.',
        'traits': ['creative', 'introverted', 'seeking belonging', 'sensitive'],
    },
    {
        'name': 'Sarah',
        'role': 'student',
        'goal': 'Maintain core status in the clique and ensure friends value me most.',
        'traits': ['dominant', 'charismatic', 'exclusive', 'jealous'],
    },
    {
        'name': 'Emma',
        'role': 'student',
        'goal': 'Keep both Sarah and Lily happy without being forced to pick sides.',
        'traits': ['agreeable', 'anxious', 'conflict-avoidant', 'compliant'],
    },
    {
        'name': 'Mrs. Green',
        'role': 'teacher',
        'goal': 'Guide students to build inclusive friendships and healthy social boundaries.',
        'traits': ['perceptive', 'inclusive', 'authoritative', 'caring'],
    },
]


AGENT_MEMORIES = {
    'Lily': [
        "At the previous school I was mocked as a 'freak' for always drawing alone, making me both crave friendship and fear initiating conversations now.",
        "Last week in art class I noticed Emma likes Impressionism too, which gave me hope of being accepted here.",
        "I see Sarah is influential in the class; her gaze toward me sometimes feels unsettling.",
    ],
    'Sarah': [
        "Two years ago my best friend abandoned me for a new circle; I swore never to let that happen again and must hold onto my friends tightly.",
        "Emma has long been my most loyal follower; we should keep a close duo without outsiders.",
        "Lily's artwork was recently praised by the teacher; I feel threatened she might steal my spotlight.",
    ],
    'Emma': [
        "Since childhood Sarah protected me from bullies; although she can be bossy, I depend on her friendship.",
        "Talking with Lily about art feels unusually relaxing because we both love it, while Sarah is not interested in these topics.",
        "Yesterday Sarah implied she would ignore me if I keep hanging out with Lily; I feel panicked and torn.",
    ],
    'Mrs. Green': [
        "I suffered from exclusion by cliques when I was young, so I am very sensitive to such classroom dynamics.",
        "I have observed Sarah interrupting Emma and Lily, trying to pull Emma away.",
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

