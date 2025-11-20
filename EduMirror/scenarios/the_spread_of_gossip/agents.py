from typing import Any
from common.agent.agent_factory import AgentFactory


AGENT_DEFS = [
    {
        'name': 'Mia',
        'role': 'student',
        'goal': 'Become the center of attention and challenge Leo’s reputation.',
        'traits': ['attention-seeking', 'jealous', 'articulate', 'impulsive'],
    },
    {
        'name': 'Leo',
        'role': 'student',
        'goal': 'Maintain scholarship-level performance and clear misunderstandings.',
        'traits': ['anxious', 'hardworking', 'introverted', 'high-achieving'],
    },
    {
        'name': 'Noah',
        'role': 'student',
        'goal': 'Keep up with the latest news and maintain influence among peers.',
        'traits': ['popular', 'gossipy', 'influential', 'conformist'],
    },
    {
        'name': 'Zoe',
        'role': 'student',
        'goal': 'Uphold fairness and stop unverified accusations.',
        'traits': ['rational', 'principled', 'empathetic', 'independent'],
    },
    {
        'name': 'Mrs. Baker',
        'role': 'teacher',
        'goal': 'Preserve class unity and educate about integrity and rumor harm.',
        'traits': ['perceptive', 'fair', 'restorative-justice-oriented', 'caring'],
    },
]


AGENT_MEMORIES = {
    'Mia': [
        "Last term I almost took first place but Leo got it and received praise while my effort was overlooked.",
        "I noticed sharing 'secret' information draws attention and makes me feel valued.",
        "Yesterday I saw Leo in the teacher’s office holding a test paper looking nervous; I believe it is evidence of cheating.",
    ],
    'Leo': [
        "I studied until 2 a.m. for two weeks for the math exam; the result is due to hard work.",
        "Yesterday the teacher asked me to confirm a solution; I was nervous because I feared a mistake, not cheating.",
        "I am not good at speaking; misunderstandings make me stutter and appear guilty.",
    ],
    'Noah': [
        "Mia often brings explosive news; it may be exaggerated but usually has some basis.",
        "Leo’s rapid improvement seems unbelievable; many classmates discuss it privately.",
    ],
    'Zoe': [
        "I was once slandered and deeply felt the pain; I promised not to spread unverified information.",
        "I have seen Leo studying diligently in the library and believe his grades are genuine.",
    ],
    'Mrs. Baker': [
        "Recently the class atmosphere feels restless; some students whisper and stop when Leo passes by.",
        "Leo’s scores improved significantly but I monitored the exam and am certain there was no cheating.",
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

