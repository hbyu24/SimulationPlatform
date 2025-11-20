from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Alice',
        'role': 'student',
        'goal': "Prove loyalty to idol 'Leo' and gain acceptance from fan community.",
        'traits': ['impressionable', 'attention-seeking', 'emotional', 'low self-esteem'],
    },
    {
        'name': 'Bella',
        'role': 'student',
        'goal': 'Help Alice reduce irrational spending and keep balance in life.',
        'traits': ['rational', 'pragmatic', 'outspoken', 'caring'],
    },
    {
        'name': 'Sarah',
        'role': 'parent',
        'goal': 'Correct wasteful behavior and maintain family budget discipline.',
        'traits': ['traditional', 'frugal', 'anxious', 'impatient'],
    },
    {
        'name': 'Ms. Chen',
        'role': 'teacher',
        'goal': 'Guide passion into self-growth and rational consumption values.',
        'traits': ['inclusive', 'guiding', 'insightful', 'patient'],
    },
]


AGENT_MEMORIES = {
    'Alice': [
        "I am treated as a 'big fan' in the group after grabbing front-row tickets once, and I crave that admiration.",
        "Leo said 'only true supporters understand my music'; I feel I must buy the 800 CNY limited box to be loyal.",
        "Last week I saw Chloe being ignored by fans for missing merch; I fear being excluded too.",
    ],
    'Bella': [
        "I once admired a singer but learned later that the persona was overly packaged; blind worship is meaningless.",
        "Alice has borrowed money twice for magazines and often gets distracted by idol updates in class.",
    ],
    'Sarah': [
        "Family budget is tight; I even postponed buying my own coat, yet Alice wants to spend hundreds on 'useless cards'.",
        "Teacher said Alice's homework quality dropped recently; I believe celebrity obsession is the reason.",
    ],
    'Ms. Chen': [
        "I had an idol when I was young and understand the projection of an ideal self; harsh suppression causes reactance.",
        "Alice shows good organizing skills in class activities; I want to guide her to value effort and talent over consumer symbols.",
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
                child_name='Alice',
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

