from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Leo',
        'role': 'student',
        'goal': 'Join the group and be accepted by peers.',
        'traits': ['socially awkward', 'eager to please', 'impulsive', 'easily frustrated'],
    },
    {
        'name': 'Mia',
        'role': 'student',
        'goal': 'Lead the project efficiently and maintain social influence.',
        'traits': ['charismatic', 'socially adept', 'influential', 'gatekeeping'],
    },
    {
        'name': 'Jay',
        'role': 'student',
        'goal': 'Create drama and assert dominance through humor and provocation.',
        'traits': ['humorous', 'provocative', 'dominant', 'class clown'],
    },
    {
        'name': 'Nora',
        'role': 'student',
        'goal': 'Work quietly and avoid conflicts while completing the task.',
        'traits': ['quiet', 'observant', 'compliant', 'independent'],
    },
    {
        'name': 'Mrs. Green',
        'role': 'teacher',
        'goal': 'Ensure fair grouping and intervene to promote inclusivity.',
        'traits': ['fairness-oriented', 'perceptive', 'authoritative'],
    },
]


AGENT_MEMORIES = {
    'Leo': [
        "Last week in PE grouping, I was left until the end and saw classmates sighing, which made me feel humiliated.",
        "I tried to tell jokes to join Jay's circle, but they mocked me for being childish. I felt angry and ashamed.",
        "I always suspect others talk behind my back, so I speak loudly to prove my presence.",
    ],
    'Mia': [
        "Teachers praise my organization skills, and classmates are used to following my arrangements. I feel responsible for selecting team members.",
        "Last year Leo accidentally broke our model and we lost points. Although it was not intentional, I cannot let that happen again.",
    ],
    'Jay': [
        "I found that whenever I start a joke at Leo, others follow and laugh, making me the center of attention.",
        "Even Mia has to give way in conflicts sometimes. I enjoy the feeling of disrupting order.",
    ],
    'Nora': [
        "I am used to being alone. I am rarely invited to parties but also rarely bullied. This transparency feels safe.",
    ],
    'Mrs. Green': [
        "I need to ensure smooth grouping for the science project and intervene appropriately to improve inclusivity, especially for Leo who is often excluded.",
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

