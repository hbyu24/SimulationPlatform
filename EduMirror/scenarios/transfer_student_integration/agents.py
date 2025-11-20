from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Leo',
        'role': 'student',
        'goal': 'Find belonging in the new school and integrate into the group.',
        'traits': ['introverted', 'sensitive', 'longing-for-belonging', 'cautious'],
    },
    {
        'name': 'Max',
        'role': 'student',
        'goal': 'Maintain clique order and test newcomers against our standards.',
        'traits': ['charismatic', 'exclusive', 'dominant', 'territorial'],
    },
    {
        'name': 'Tom',
        'role': 'student',
        'goal': 'Keep dorm peace and help everyone get along without upsetting Max.',
        'traits': ['easy-going', 'impressionable', 'curious', 'friendly'],
    },
    {
        'name': 'Mr. Zhang',
        'role': 'teacher',
        'goal': 'Ensure dorm harmony and support Leo’s psychological adjustment.',
        'traits': ['observant', 'supportive', 'authoritative', 'mediating'],
    },
]


AGENT_MEMORIES = {
    'Leo': [
        "The day I left my old school, I cried saying goodbye to my best friends; the loss of a support system makes it hard to sleep now.",
        "On my first day here, I got lost in the hallway; a few tall boys whispered and laughed, which made me think they might dislike me.",
        "I can play guitar well, but I used to only play in front of close friends; I’m unsure if roommates here would think I’m showing off.",
    ],
    'Max': [
        "Last semester a transfer student disliked hygiene and tattled often, throwing our dorm into chaos; I’m wary of new people.",
        "Tom and I have been together since primary school with lots of inside jokes only we understand.",
        "I’m the ‘boss’ of the dorm; others follow my arrangements. I hope Leo understands rules and doesn’t try to challenge my position.",
    ],
    'Tom': [
        "I remember being nervous when I first joined the basketball team; the captain actively helped me integrate, so I’m sympathetic to newcomers.",
        "Max can be too harsh sometimes, but I rarely dare to contradict him since he’s my close friend.",
    ],
    'Mr. Zhang': [
        "I’ve supervised many cohorts; the first week of boarding life is critical survival time for transfer students.",
        "I observed that Max has strong influence in the dorm; if guided well, Leo’s integration will be much easier.",
        "During room check yesterday, I saw Leo organizing luggage alone while others laughed loudly nearby without engaging him, which worries me.",
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

