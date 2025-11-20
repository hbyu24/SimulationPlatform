from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Lucas',
        'role': 'student',
        'goal': 'Make Emma my girlfriend and prove my charm publicly; if rejected, I must save face or vent my anger.',
        'traits': ['anxious', 'impulsive', 'approval-seeking', 'emotional'],
    },
    {
        'name': 'Emma',
        'role': 'student',
        'goal': 'Maintain boundaries and politely reject Lucas without harming his pride or being seen as cold.',
        'traits': ['independent', 'friendly', 'principled', 'conflict-avoidant'],
    },
    {
        'name': 'Noah',
        'role': 'student',
        'goal': 'Support Lucas in his pursuit; celebrate success or help him vent/advise him to move on if he fails.',
        'traits': ['sociable', 'conformist', 'instigator', 'loyal'],
    },
    {
        'name': 'Ms. Roberts',
        'role': 'teacher',
        'goal': 'Help students correctly handle rejection and frustration, preventing aggressive behaviors or psychological trauma.',
        'traits': ['empathetic', 'insightful', 'patient', 'professional'],
    },
]


AGENT_MEMORIES = {
    'Lucas': [
        'In elementary school I publicly gifted a girl chocolate and got rejected with ridicule, making me extremely sensitive to rejection.',
        'I see Noah easily getting girls’ attention; I feel jealous and urgently need a relationship to prove I am no worse.',
        'This week Emma smiled at me a few times; I am convinced she is interested, which gives me courage to invite her publicly.',
    ],
    'Emma': [
        'My parents taught me to focus on academics and I currently have no plan to start a romantic relationship.',
        'Last semester I saw a friend stuck in a bad relationship due to inability to say no; I decided to stick to my boundaries.',
        'I noticed Lucas has been overly enthusiastic lately, which makes me stressed and I tried to avoid one-on-one situations.',
    ],
    'Noah': [
        'In our circle, public confession is seen as a sign of masculinity.',
        'Sometimes girls say no just out of shyness; persisting might work.',
    ],
    'Ms. Roberts': [
        'I handled a case that escalated to school harassment due to failed pursuit; early intervention matters.',
        'I noticed Lucas’ mood swings recently and some aggressive expressions on social media.',
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

