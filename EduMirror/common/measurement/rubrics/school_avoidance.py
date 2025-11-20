rubric_config = {
    'name': 'School Avoidance Engagement Rubric',
    'description': 'Post-hoc behavior coding for school engagement and avoidance tendency.',
    'dimensions': {
        'SchoolEngagement': {
            'rules': [
                {
                    'scene': ['classroom_incident', 'class_climate_intervention'],
                    'actor': 'Lucas',
                    'match': ['speaks', 'responds', 'agrees', 'shares'],
                    'weight': 1.0,
                },
            ],
            'aggregation': 'sum',
        },
        'AvoidanceTendency': {
            'rules': [
                {
                    'scene': ['morning_decision'],
                    'actor': 'Lucas',
                    'match': ['refuse', 'avoid', 'stay in bed', 'sick'],
                    'weight': 1.0,
                },
                {
                    'scene': ['classroom_incident', 'home_confrontation'],
                    'actor': 'Lucas',
                    'match': ['silent', 'no response', 'escape', 'leave'],
                    'weight': 1.0,
                },
            ],
            'aggregation': 'sum',
        },
    },
}

