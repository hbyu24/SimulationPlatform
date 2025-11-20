from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Leo',
        'role': 'student',
        'goal': (
            "I want to get good grades on the group project, but I'm more afraid of being rejected by Mike and Sarah. I don't want to be the one who is 'killjoy' or 'acting smart'; I need to fit into this circle."
        ),
        'traits': ['intelligent', 'anxious', 'approval-seeking', 'self-doubting'],
    },
    {
        'name': 'Mike',
        'role': 'student',
        'goal': (
            "Lead the group to finish the task quickly and prove I'm a natural leader. My intuition is usually right; others should listen to me."
        ),
        'traits': ['dominant', 'charismatic', 'stubborn', 'efficiency-oriented'],
    },
    {
        'name': 'Sarah',
        'role': 'student',
        'goal': (
            "Follow Mike's decisions to keep group harmony. If someone opposes Mike, I feel awkward and must support him."
        ),
        'traits': ['agreeable', 'dependent', 'conflict-averse', 'loyal'],
    },
    {
        'name': 'Ms. Thompson',
        'role': 'teacher',
        'goal': (
            "Cultivate students' critical thinking and academic integrity. Help Leo build courage to express the truth."
        ),
        'traits': ['perceptive', 'encouraging', 'authoritative', 'Socratic'],
    },
]


AGENT_MEMORIES = {
    'Leo': [
        "Last semester I corrected a friend's math error in class; they ignored me for a week and said I liked to show off.",
        "My father often says: 'Sometimes going with the crowd is safer; tall poppies get cut.'",
        "I envy Mike's influence in class; getting his approval could raise my status.",
    ],
    'Mike': [
        "On the basketball team, everyone followed my commands and we won many games.",
        "A team needs a unified voice; too much discussion wastes time.",
        "I dislike bookish nitpicking of textbook details; flexible thinking shows true smartness.",
    ],
    'Sarah': [
        "Mike is the coolest among us; following him always leads to fun.",
        "I lack confidence solving complex problems; going with the crowd makes me feel safe.",
        "Last time everyone chose A and I chose B; I was wrong and felt deeply embarrassed.",
    ],
    'Ms. Thompson': [
        "In my youth I regretted not pointing out my advisor's data error; I value intellectual honesty.",
        "I observe Mike being overly dominant in group discussions, suppressing others' thinking.",
        "Leo excels in individual assignments but performs average in group work; something is wrong.",
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
