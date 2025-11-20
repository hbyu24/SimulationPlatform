from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Alex',
        'role': 'student',
        'goal': 'Maintain dignity while balancing social needs and family responsibilities.',
        'traits': ['sensitive', 'conscientious', 'conflict-avoidant', 'proud'],
    },
    {
        'name': 'Ben',
        'role': 'student',
        'goal': 'Coordinate activities that suit everyone and preserve friendship.',
        'traits': ['easy-going', 'sociable', 'budget-conscious', 'understanding'],
    },
    {
        'name': 'Chloe',
        'role': 'student',
        'goal': 'Share memorable experiences to strengthen friendships.',
        'traits': ['confident', 'generous', 'price-insensitive', 'enthusiastic', 'occasionally oblivious'],
    },
    {
        'name': 'Sam',
        'role': 'parent',
        'goal': 'Balance family basic needs with supporting child social development.',
        'traits': ['stressed', 'irritable', 'family-oriented', 'proud', 'hardworking'],
    },
    {
        'name': 'Mr. Davis',
        'role': 'teacher',
        'goal': 'Create an inclusive classroom and support students facing social challenges.',
        'traits': ['observant', 'empathetic', 'proactive', 'communicative', 'fair'],
    },
]


AGENT_MEMORIES = {
    'Alex': [
        "Last year I quit the school basketball team because I couldn't afford gear and travel; I told friends it was due to study workload.",
        "Last month I saw my father calculating bills late at night and realized our situation is worse than I thought; I decided to cut my expenses.",
        "Last week when Chloe talked about her overseas trip, I felt both envy and inferiority and pretended to be interested despite discomfort.",
    ],
    'Ben': [
        "Last summer our family planned and saved for months to afford a beach vacation.",
        "I noticed Alex often hesitates for activities involving spending; I suspect he faces financial pressure and think about caring for his feelings.",
        "I once organized a free park picnic; it was our happiest gathering and showed me that friendship is about time together, not money.",
    ],
    'Chloe': [
        "We travel abroad almost every long holiday; last birthday my parents took me to ski in Switzerland.",
        "My dad once gave me his credit card for a concert and said not to worry about money.",
        "When I proposed a high-end restaurant last month, Alex looked uneasy; I wasn’t sure why or how to ask without offending.",
    ],
    'Sam': [
        "Three months ago I was laid off and am still looking for work; I worry about rent and bills every night.",
        "Last week I borrowed money from relatives to pay Alex’s tuition, which felt humiliating.",
        "Yesterday when Alex mentioned a weekend plan with classmates, I saw expectation in his eyes and felt both heartache and guilt.",
    ],
    'Mr. Davis': [
        "I once was a student who could not attend many school activities due to financial hardship.",
        "Last semester I noticed Alex withdrawing in social activities and discomfort around paid events.",
        "At a recent parents’ meeting I learned Alex’s family faces serious financial stress and decided to pay closer attention.",
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