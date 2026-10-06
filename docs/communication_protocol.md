# Blackboard Communication Protocol

ScholarPlan records KQML-inspired performatives in the SQLite `messages` table.

| Performative | Meaning in ScholarPlan |
|---|---|
| `request` | Planner requests a revised retrieval action |
| `inform` | An agent publishes a new artefact or result |
| `confirm` | Critic confirms that claims are source-supported |
| `reject` | Critic rejects unsupported claims |

This is intentionally a lightweight protocol rather than a full KQML parser. It
connects the implementation to Unit 6 agent communication concepts while keeping
the ReAct/blackboard control flow inspectable.
