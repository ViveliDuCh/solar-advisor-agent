from solar_agent.agent_client import agent_framework_mode


def test_agent_framework_mode_is_offline_without_credentials(monkeypatch) -> None:
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert agent_framework_mode() == "offline"


def test_agent_framework_mode_requires_both_foundry_values(monkeypatch) -> None:
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://example.invalid/project")
    monkeypatch.delenv("FOUNDRY_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert agent_framework_mode() == "offline"
