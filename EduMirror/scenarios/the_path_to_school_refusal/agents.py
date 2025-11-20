from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Lucas',
        'role': 'student',
        'goal': 'Avoid school due to fear, shame, and desire to escape pressure.',
        'traits': ['anxious', 'low self-esteem', 'introverted', 'sensitive'],
    },
    {
        'name': 'Sarah',
        'role': 'parent',
        'goal': 'Ensure academic progress through strict discipline for future success.',
        'traits': ['high-expectation', 'anxious', 'authoritarian', 'caring but misguided'],
    },
    {
        'name': 'Mr. Thompson',
        'role': 'teacher',
        'goal': 'Maintain standards and later provide emotional support to at-risk students.',
        'traits': ['rigorous', 'traditional', 'insightful', 'supportive'],
    },
    {
        'name': 'Leo',
        'role': 'student',
        'goal': 'Seek attention and status by belittling weaker peers.',
        'traits': ['dominant', 'mean', 'popular'],
    },
]


AGENT_MEMORIES = {
    'Lucas': [
        "Last month I failed the math midterm and the teacher read my score aloud; I felt everyone was laughing at me and wanted to vanish.",
        "I tried to tell my parents I could not follow the class, but they said I was not working hard enough; I felt no one understood my helplessness.",
        "Yesterday I bumped into Leo in the hallway; he humiliated me publicly and others laughed; I felt isolated and terrified.",
    ],
    'Sarah': [
        "I suffered for years due to low education and want Lucas to be better than me.",
        "Lucas has been gloomy recently; I worry he is distracted by games, so I tightened supervision and confiscated devices.",
    ],
    'Mr. Thompson': [
        "I noticed Lucas becoming increasingly silent in class with deteriorating homework quality.",
        "A recent training on school avoidance signs reminded me of Lucas; I reflected on being too harsh.",
    ],
    'Leo': [
        "Lucas looks timid and is easy to tease; making fun of him gets laughs and boosts my status.",
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
                child_name='Lucas',
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

