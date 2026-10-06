from scholarplan.providers.mock import MockLLMProvider

def test_critic_supports_grounded_claim():
    p = MockLLMProvider()
    result = p.verify_claim(
        "Blackboard systems coordinate agents through shared state.",
        "Blackboard systems coordinate agents through shared state."
    )
    assert result["label"] == "SUPPORTED"

def test_critic_rejects_unrelated_claim():
    p = MockLLMProvider()
    result = p.verify_claim(
        "SQLite prevents hallucination in all language models.",
        "SQLite is a transactional embedded database."
    )
    assert result["label"] == "UNSUPPORTED"
