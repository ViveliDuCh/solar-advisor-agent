from __future__ import annotations

import os

from agent_framework import SupportsChatGetResponse
from dotenv import load_dotenv


class AgentConfigurationError(RuntimeError):
    pass


def agent_framework_mode() -> str:
    load_dotenv()
    if os.getenv("FOUNDRY_PROJECT_ENDPOINT") and os.getenv("FOUNDRY_MODEL"):
        return "foundry"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "offline"


def create_chat_client() -> SupportsChatGetResponse:
    mode = agent_framework_mode()
    if mode == "foundry":
        from agent_framework.foundry import FoundryChatClient
        from azure.identity import AzureCliCredential

        return FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL"],
            credential=AzureCliCredential(),
        )
    if mode == "openai":
        from agent_framework.openai import OpenAIChatClient

        return OpenAIChatClient()
    raise AgentConfigurationError(
        "Agent Framework is installed, but no chat model is configured. Set "
        "FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL, then authenticate with Azure CLI."
    )
