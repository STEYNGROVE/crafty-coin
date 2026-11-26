import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

vision=json.loads(
    (ROOT/"core/vision.json").read_text()
)

activities=[
    [
        "Remember three familiar objects.",
        "Recall a short sequence after a break.",
        "Compare two active recall methods."
    ],
    [
        "Find a matching shape.",
        "Find differences between two drawings.",
        "Complete a distraction-free planning task."
    ],
    [
        "Sort objects by shape.",
        "Complete a number pattern.",
        "Explain the reasoning behind a decision."
    ],
    [
        "Draw an imaginary animal.",
        "Invent three uses for a cardboard box.",
        "Design a solution to an everyday problem."
    ],
    [
        "Arrange shapes into a picture.",
        "Draw a simple room from above.",
        "Design a model using spatial constraints."
    ],
    [
        "Tell a short story.",
        "Explain how something works.",
        "Present two sides of a fictional debate."
    ],
    [
        "Copy gentle hand movements.",
        "Practise a comfortable movement sequence.",
        "Design a safe coordination exercise."
    ],
    [
        "Name a feeling.",
        "Describe how a fictional character feels.",
        "Explore healthy responses to everyday stress."
    ],
    [
        "Find a way through a simple maze.",
        "Solve a paper construction challenge.",
        "Compare solutions under resource constraints."
    ],
    [
        "Sort objects using a different rule.",
        "Find another solution to a puzzle.",
        "Revise a plan when requirements change."
    ],
    [
        "Put three daily tasks in order.",
        "Plan a small creative project.",
        "Create a project schedule with milestones."
    ],
    [
        "Practise taking turns.",
        "Plan a cooperative activity.",
        "Resolve a fictional team disagreement."
    ]
]

heroes=vision["superheroes"]

assert len(heroes)==len(activities)==12

levels=[
    ("DISCOVER",4,7),
    ("EXPLORER",8,12),
    ("FUTURE",13,17)
]

challenges=[]

for n,hero in enumerate(heroes,1):

    for i,(level,low,high) in enumerate(levels):

        challenges.append({
            "id":f"SQUAD-{n:02d}-{level}",
            "leader":"Crafty",
            "hero":hero["name"],
            "skill":hero["skill"],
            "level":level,
            "minimumAge":low,
            "maximumAge":high,
            "activity":activities[n-1][i],
            "reflection":
                "Describe what you tried and learned.",
            "difficultyOptions":[1,2,3],
            "optional":True,
            "offlineAvailable":True,
            "financialReward":False,
            "cryptoReward":False,
            "liveAIRequired":False,
            "status":"INTRODUCTORY_DRAFT"
        })

assert len(challenges)==36

(ROOT/"squad/challenges.json").write_text(
    json.dumps(challenges,indent=2)
)

print("PASS: Crafty leads twelve superheroes")
print("PASS: 36 age-specific challenges")
