import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

vision=json.loads(
    (ROOT/"core/vision.json").read_text()
)

topics=[
("Memory",
 "Remember three objects",
 "Create a memory map",
 "Compare two revision strategies"),
("Understanding emotions",
 "Name three feelings",
 "Explore different perspectives",
 "Evaluate thinking habits"),
("Everyday wellbeing",
 "Practise calm breathing",
 "Design a balanced daily routine",
 "Create a healthy stress-management plan"),
("The human body",
 "Identify five body parts",
 "Explore how muscles work",
 "Explain how body systems cooperate"),
("Physical activity",
 "Practise gentle balance movements",
 "Design a safe movement circuit",
 "Plan a gradual fitness routine"),
("Computer science",
 "Arrange instructions in order",
 "Create a simple algorithm",
 "Build and debug a small program"),
("Online safety",
 "Identify a trusted adult",
 "Recognize suspicious messages",
 "Analyse a fictional phishing attempt"),
("Scientific thinking",
 "Observe an everyday object",
 "Compare floating and sinking",
 "Design a controlled experiment"),
("Engineering",
 "Build a paper tower",
 "Design a paper bridge",
 "Compare structural design alternatives"),
("Creative expression",
 "Draw an imaginary world",
 "Create a visual story",
 "Develop an original design portfolio"),
("Communication",
 "Tell a short story",
 "Explain a process clearly",
 "Write a structured argument"),
("Mathematical reasoning",
 "Count and group objects",
 "Solve a measurement challenge",
 "Compare mathematical models"),
("Money skills",
 "Sort needs and wants",
 "Plan a fictional shopping budget",
 "Build a simulated monthly budget"),
("Entrepreneurship",
 "Invent an imaginary shop",
 "Design a fictional product",
 "Evaluate a simulated business model"),
("Leadership",
 "Practise taking turns",
 "Plan a team challenge",
 "Resolve a fictional team disagreement"),
("Personal safety",
 "Identify safe helpers",
 "Practise an emergency help message",
 "Develop a household safety checklist"),
("Environmental responsibility",
 "Sort reusable materials",
 "Observe local plant life",
 "Design a resource-saving project"),
("Independent living",
 "Organize your belongings",
 "Plan a household task",
 "Create an independent living checklist"),
("Geography and cultures",
 "Draw a map of a room",
 "Explore a country's geography",
 "Compare cultural perspectives"),
("Career exploration",
 "Draw a future job",
 "Explore three occupations",
 "Research a career learning pathway"),
("Road safety",
 "Recognize pedestrian signals",
 "Identify road hazards in pictures",
 "Evaluate fictional road scenarios"),
("Ethical reasoning",
 "Practise sharing fairly",
 "Discuss a fictional dilemma",
 "Compare competing ethical choices")
]

assert len(topics)==len(vision["academies"])==22

levels=[
    ("DISCOVER",4,7),
    ("EXPLORER",8,12),
    ("FUTURE",13,17)
]

missions=[]

for index,(academy,topic) in enumerate(
    zip(vision["academies"],topics),1
):
    subject,*activities=topic

    for level,minimum,maximum in levels:

        activity=activities[
            ["DISCOVER","EXPLORER","FUTURE"].index(level)
        ]

        missions.append({
            "id":f"ACA-{index:02d}-{level}",
            "academy":academy,
            "character":"Crafty",
            "level":level,
            "minimumAge":minimum,
            "maximumAge":maximum,
            "topic":subject,
            "objective":activity,
            "introduction":
                f"Explore {subject} with Crafty.",
            "activity":activity,
            "reflection":
                "Explain what you learned in your own words.",
            "assessment":
                "Describe one idea and how you could use it.",
            "adultSupport":
                "Ask a trusted adult for help when needed.",
            "offlineAvailable":True,
            "liveAIRequired":False,
            "financialReward":False,
            "cryptoEnabled":False,
            "status":"INTRODUCTORY_DRAFT"
        })

assert len(missions)==66

(ROOT/"education/curriculum.json").write_text(
    json.dumps(missions,indent=2)
)

print("PASS: 22 academies")
print("PASS: 66 introductory missions")
print("PASS: Three age pathways")
