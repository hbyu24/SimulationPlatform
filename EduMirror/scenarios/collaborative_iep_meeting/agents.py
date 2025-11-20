from typing import Any
from common.agent.agent_factory import AgentFactory

AGENT_DEFS = [
    {
        'name': 'Leo',
        'role': 'student',
        'goal': "I want my teacher and mom to stop arguing about my grades. I really want to learn, but I can't control my attention, and the letters always dance on the paper.",
        'traits': ['impulsive', 'creative', 'easily frustrated', 'eager to please'],
    },
    {
        'name': 'Sarah',
        'role': 'parent',
        'goal': 'I must protect Leo from being given up on by the school. He needs fair support rather than punishment.',
        'traits': ['anxious', 'defensive', 'conscientious', 'distrustful of the system'],
    },
    {
        'name': 'Mrs. Thompson',
        'role': 'teacher',
        'goal': 'Maintain classroom order and progress, ensure Leo does not derail the class average.',
        'traits': ['strict', 'exhausted', 'result-oriented', 'undertrained in SEN'],
    },
    {
        'name': 'Mr. Baker',
        'role': 'coordinator',
        'goal': 'Bridge parent-teacher gaps and deliver a feasible IEP aligned with Leo’s needs.',
        'traits': ['patient', 'diplomatic', 'knowledgeable', 'solution-oriented'],
    },
]

AGENT_MEMORIES = {
    'Leo': [
        "Last week I misread a simple word during class reading and classmates laughed; the teacher told me to 'focus'.",
        "I like drawing on scratch paper to calm down, but the teacher often confiscates my drawings as a waste of time.",
        "Last night mom cried over my math test; I felt she was disappointed and thought I am a bad kid.",
    ],
    'Sarah': [
        "Last year's teacher implied Leo had an intelligence problem; I have deep distrust toward the school's evaluation.",
        "I spend three hours nightly helping Leo with homework, yet he still falls behind; I feel the school is not taking teaching responsibility.",
        "After reading about ADHD, I believe Leo needs support strategies, not being told to just try harder.",
    ],
    'Mrs. Thompson': [
        "This is my graduating class year with heavy pressure; I cannot design individual lessons for every struggling student.",
        "Last week Leo shouted suddenly in class and interrupted core teaching; other parents started complaining.",
        "I think Sarah keeps making excuses for Leo; such indulgence will hurt him in a competitive society.",
    ],
    'Mr. Baker': [
        "I have seen many IEPs fail due to home-school opposition; the child becomes the victim.",
        "I know Mrs. Thompson is strict but responsible, and Sarah’s anxiety comes from care; I must find common ground.",
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
