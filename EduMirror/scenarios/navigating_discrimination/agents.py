from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Maya',
        'role': 'student',
        'goal': 'Showcase cultural heritage in the group project and be valued while fitting in.',
        'traits': ['intelligent', 'culturally proud', 'sensitive', 'eager to fit in', 'anxious'],
    },
    {
        'name': 'Liam',
        'role': 'student',
        'goal': 'Lead the team to the highest score with familiar, “safe” topics and avoid “weird” ideas.',
        'traits': ['dominant', 'popular', 'culturally insensitive', 'competitive', 'humorous but mean'],
    },
    {
        'name': 'Sarah',
        'role': 'student',
        'goal': 'Maintain good relationships and avoid conflict, keep the atmosphere comfortable.',
        'traits': ['friendly', 'conflict-avoidant', 'conformist', 'empathetic'],
    },
    {
        'name': 'Ms. Thompson',
        'role': 'teacher',
        'goal': 'Ensure safety and respect for all students and cultivate inclusive understanding and empathy.',
        'traits': ['fair', 'observant', 'committed to inclusion', 'authoritative'],
    },
]


AGENT_MEMORIES = {
    'Maya': [
        "Last month some classmates said my traditional lunch smelled weird, and I threw it away.",
        "My parents told me I must work twice as hard to gain respect.",
        "I am good at history and art and want to use this knowledge in the Global Culture Fair project.",
    ],
    'Liam': [
        "I won last year's debate by insisting on my viewpoint and overwhelming the opponent.",
        "In my social circle we make all kinds of jokes; if someone gets upset, they are too sensitive.",
        "I think the normal standard is what most people do; deviating is risky.",
    ],
    'Sarah': [
        "I was excluded for a week for supporting the weaker side in a dispute; it made me afraid to take sides.",
        "I find Maya interesting, but Liam is the most popular boy; I do not want to offend him.",
    ],
    'Ms. Thompson': [
        "I attended a workshop on culturally responsive teaching and realized many implicit biases harm students.",
        "I noticed Maya became withdrawn recently, while Liam often dominates group discussions.",
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
                child_name='Maya',
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

