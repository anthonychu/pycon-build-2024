import os
from datetime import datetime, timedelta, timezone

import chainlit as cl
import dotenv
import langchain.agents
from azure.identity import DefaultAzureCredential
from langchain import hub
from langchain.agents import AgentExecutor
from langchain.tools.retriever import create_retriever_tool
from langchain_azure_dynamic_sessions import SessionsPythonREPLTool
from langchain_openai import AzureChatOpenAI

from database import doc_store

dotenv.load_dotenv()


@cl.on_chat_start
async def on_chat_start():

    azure_token = None
    def token_factory():
        nonlocal azure_token
        if azure_token is None or datetime.fromtimestamp(azure_token.expires_on, timezone.utc) < datetime.now(timezone.utc) + timedelta(minutes=5):
            print("Refreshing Azure token...")
            azure_token = DefaultAzureCredential().get_token("https://cognitiveservices.azure.com/.default")
        return azure_token.token

    llm = AzureChatOpenAI(
        azure_deployment="gpt-35-turbo",
        openai_api_version="2023-09-15-preview",
        streaming=True,
        temperature=0,
        azure_ad_token_provider=token_factory,
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    )

    retriever = doc_store.as_retriever()

    retriever_tool = create_retriever_tool(
        retriever,
        "search_documents",
        "Searches and returns excerpts from documents that contain useful information.",
    )

    code_interpreter_tool = SessionsPythonREPLTool(
        pool_management_endpoint=os.environ["POOL_MANAGEMENT_ENDPOINT"],
    )

    tools = [retriever_tool, code_interpreter_tool]
    react_agent = langchain.agents.create_react_agent(
        llm=llm,
        tools=tools,
        prompt=hub.pull("hwchase17/react"),
    )

    react_agent_executor = AgentExecutor(agent=react_agent, tools=tools, verbose=True, handle_parsing_errors=True, return_intermediate_steps=True)

    cl.user_session.set("agent", react_agent_executor)

@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")

    message_content = message.content

    res = await agent.ainvoke(
        input={"input": message_content},
        config={"configurable": {"session_id": "---"}},
    )

    async with cl.Step(name="AgentExecutor") as step:
        step.output = '\n'.join([a[0].log for a in res['intermediate_steps']])

    await cl.Message(content=res['output']).send()

