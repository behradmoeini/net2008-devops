import itertools
import random
import time

excuses = [
    "It works on my machine.",
    "Have you tried turning it off and on again?",
    "It is always DNS.",
    "I did not touch anything. It was like that.",
    "The network is fine. The network is always fine.",
    "Let me check the logs. Oh. These are the logs.",
    "That is not a bug. That is a feature request.",
    "It was working yesterday.",
]

print("Intern started. Ticket queue: 0. Coffee level: 100%", flush=True)
for ticket in itertools.count(1):
    print(f"ticket #{ticket}: {random.choice(excuses)}", flush=True)
    time.sleep(2)
