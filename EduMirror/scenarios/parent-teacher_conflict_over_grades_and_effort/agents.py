from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Jordan',
        'role': 'student',
        'goal': 'Protect motivation and dignity while explaining effort despite disappointing grades.',
        'traits': ['diligent', 'anxious', 'compliant', 'insecure'],
    },
    {
        'name': 'Taylor',
        'role': 'parent',
        'goal': 'Ensure high academic outcomes and demand accountability when grades slip.',
        'traits': ['achievement-oriented', 'controlling', 'protective', 'impatient'],
    },
    {
        'name': 'Ms. Lee',
        'role': 'teacher',
        'goal': 'De-escalate conflict and reframe the issue as strategy and method rather than attitude.',
        'traits': ['patient', 'professional', 'growth-minded', 'observant'],
    },
]


AGENT_MEMORIES = {
    'Jordan': [
        "Last math exam I studied hard for a week but only got a C; my mother said I must have been daydreaming, which made me feel wronged and silent.",
        "In class I feel slower than others; although Ms. Lee encourages questions, I avoid asking because I fear peers think I am dumb.",
        "Tonight I need to show the midterm report card to my father; my stomach hurts because I know I messed up the science test again.",
    ],
    'Taylor': [
        "My partner and I graduated from elite schools; we know competition is brutal and believe falling behind now kills future opportunities.",
        "I enrolled Jordan in expensive tutoring and supervise study until 10pm; if grades do not improve, the school teaching must be the problem.",
        "In the parent chat I saw other kids getting As; the comparison triggers deep anxiety and anger.",
    ],
    'Ms. Lee': [
        "I observe Jordan working very hard but relying on memorization without logical application; this causes point loss.",
        "At the last parent meeting Taylor implied my homework load was insufficient; I realized I need to educate parents as well as students.",
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
                child_name='Jordan',
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

