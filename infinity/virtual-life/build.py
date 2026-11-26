import json
from pathlib import Path

worlds={
    "CITY":("Crafty City",[
        "Design a neighbourhood",
        "Plan a community park",
        "Allocate community resources"]),
    "FARM":("Crafty Farm",[
        "Plant an imaginary garden",
        "Plan seasonal crops",
        "Compare farming strategies"]),
    "BUSINESS":("Crafty Business",[
        "Create an imaginary shop",
        "Design a fictional product",
        "Evaluate a fictional business budget"]),
    "HOME":("Crafty Home",[
        "Organize a virtual room",
        "Plan household responsibilities",
        "Plan independent living"]),
    "ENGINEERING":("Crafty Engineering",[
        "Build a paper model",
        "Design a model bridge",
        "Compare engineering solutions"]),
    "TECH":("Crafty Technology",[
        "Arrange instructions",
        "Design an algorithm",
        "Debug a fictional system"]),
    "DRIVING":("Crafty Driving",[
        "Recognize pedestrian signals",
        "Identify road hazards",
        "Evaluate virtual driving decisions"]),
    "FINANCE":("Crafty Finance",[
        "Sort needs and wants",
        "Plan fictional shopping",
        "Create a fictional monthly budget"]),
    "ENVIRONMENT":("Crafty Environment",[
        "Sort recyclable materials",
        "Plan water conservation",
        "Compare sustainable projects"]),
    "WELLNESS":("Crafty Wellness",[
        "Plan a balanced day",
        "Explore healthy habits",
        "Design a balanced weekly routine"]),
    "CAREERS":("Crafty Careers",[
        "Explore occupations",
        "Compare career pathways",
        "Plan career development"]),
    "DISCOVERY":("Crafty Discovery",[
        "Observe familiar objects",
        "Design a safe experiment",
        "Evaluate a scientific hypothesis"])
}

levels=[
    ("DISCOVER",4,7),
    ("EXPLORER",8,12),
    ("FUTURE",13,17)
]

missions=[]

for code,(name,activities) in worlds.items():
    for i,(level,low,high) in enumerate(levels):
        missions.append({
            "id":f"LIFE-{code}-{level}",
            "world":name,
            "guide":"Crafty",
            "level":level,
            "minimumAge":low,
            "maximumAge":high,
            "activity":activities[i],
            "simulationOnly":True,
            "realMoney":False,
            "crypto":False,
            "liveAI":False,
            "status":"INTRODUCTORY_DRAFT"
        })

assert len(missions)==36

Path(__file__).with_name("worlds.json").write_text(
    json.dumps(missions,indent=2)
)

print("PASS: 12 worlds and 36 missions")
