from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Brad',
        'role': 'student',
        'goal': 'Establish leadership status among classmates by displaying power.',
        'traits': ['dominant', 'low-empathy', 'impulsive', 'charismatic'],
    },
    {
        'name': 'Vince',
        'role': 'student',
        'goal': 'Get through each day quietly and avoid conflict with Brad.',
        'traits': ['anxious', 'low self-esteem', 'sensitive', 'passive'],
    },
    {
        'name': 'Chad',
        'role': 'student',
        'goal': 'Be part of the cool kids group by following the crowd safely.',
        'traits': ['impressionable', 'approval-seeking', 'fear of exclusion'],
    },
    {
        'name': 'Dana',
        'role': 'student',
        'goal': 'Uphold fairness and consider helping Vince while staying cautious.',
        'traits': ['empathetic', 'justice-oriented', 'cautious', 'observant'],
    },
    {
        'name': 'Ms. Thompson',
        'role': 'teacher',
        'goal': 'Maintain classroom order and safety while supporting all students.',
        'traits': ['responsible', 'occasionally overwhelmed', 'caring', 'order-seeking'],
    },
]


AGENT_MEMORIES = {
    'Brad': [
        'In my old school I was bullied for being too honest; I learned to strike first to win respect.',
        'Last week in PE I pushed Vince and everyone laughed; I felt like the center of attention.',
        "I dislike seeing people outside the group's rules; Vince's timid look annoys me.",
    ],
    'Vince': [
        'Every time I enter the classroom I feel eyes like needles on me, especially when Brad is there.',
        "Yesterday my notebook was thrown to the floor; I know who did it but I didn't tell the teacher for fear of retaliation.",
        'A friend once tried to help me and got isolated; I feel I burden others and must endure alone.',
    ],
    'Chad': [
        "I've seen how Brad treats those who disobey him; I refuse to be the next target.",
        'When I laugh at Brad’s jokes mocking others, he pats my shoulder; feeling accepted makes me secure.',
    ],
    'Dana': [
        'My mom taught me to be kind and brave, but school’s unwritten rules seem more complex.',
        "I noticed Vince eating alone in the corner; I want to invite him but fear Brad's gossip.",
    ],
    'Ms. Thompson': [
        "I once couldn't join many activities due to financial hardship when I was a student.",
        "Recently I've noticed Vince's grades dropping and silence in class; I need to act carefully.",
        'A past harsh punishment led to retaliation after class; now I am cautious about interventions.',
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