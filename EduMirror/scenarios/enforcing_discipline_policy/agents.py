from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Leo',
        'role': 'student',
        'goal': 'Avoid humiliation or suspension while seeking fair treatment and understanding.',
        'traits': ['impulsive', 'defensive', 'academically frustrated', 'seeking validation'],
    },
    {
        'name': 'Mia',
        'role': 'student',
        'goal': 'Protect hard-earned achievements and feel safe in class with sincere repair.',
        'traits': ['diligent', 'anxious', 'perfectionist', 'risk-averse'],
    },
    {
        'name': 'Mr. Lee',
        'role': 'parent',
        'goal': 'Ensure Leo is treated fairly without arbitrary suspension or permanent record stain.',
        'traits': ['protective', 'skeptical of authority', 'busy', 'pragmatic'],
    },
    {
        'name': 'Mrs. Carter',
        'role': 'teacher',
        'goal': 'Maintain classroom order and fairness while educating Leo and supporting Mia.',
        'traits': ['strict but fair', 'stressed', 'rule-abiding', 'caring'],
    },
]


AGENT_MEMORIES = {
    'Leo': [
        "Last month I failed math and was criticized publicly despite trying hard.",
        "At home father says only the weak get bullied; I learned to hide insecurity behind aggression.",
        "Yesterday I stayed up late for the science project; seeing Mia’s perfect model triggered jealousy and anger.",
    ],
    'Mia': [
        "I spent two weeks building the science model crucial for my scholarship.",
        "Previously a classmate broke my work and only received a verbal warning; I felt unprotected.",
    ],
    'Mr. Lee': [
        "I was once unfairly disciplined due to teacher misunderstanding, affecting my education.",
        "Work pressure is high; I prefer school not to call me unless it is serious.",
    ],
    'Mrs. Carter': [
        "The school recently emphasized a zero-tolerance discipline policy for property damage.",
        "Leo has seemed emotionally unstable recently; I have not had time for a deep talk.",
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
                child_name='Leo',
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
