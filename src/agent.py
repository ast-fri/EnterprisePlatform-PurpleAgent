# src/agent.py
import os
import re
import json
from typing import Dict, List, Any

from a2a.server.tasks import TaskUpdater
from a2a.types import Message, Part, TextPart, TaskState
from a2a.utils import get_message_text, new_agent_text_message

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()


def parse_tags(text: str) -> Dict[str, str]:
    """Extract XML-style tags from text."""
    tags = re.findall(r"<(.*?)>(.*?)</\1>", text, re.DOTALL)
    return {tag: content.strip() for tag, content in tags}


class BaselinePurpleAgent:
    """Baseline purple agent that uses ReACT-style reasoning to solve tasks."""
    
    def __init__(self):
        # Lazy-load LLM to avoid startup errors if API keys missing
        self._llm = None
    
    def _get_llm(self):
        """Lazy load the LLM."""
        if self._llm is None:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            
            if not api_key or not endpoint:
                raise ValueError("Missing Azure OpenAI credentials")
            
            self._llm = AzureChatOpenAI(
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
                temperature=0,
            )
        return self._llm
    
    async def _generate_action(
            self,
            task: str,
            tools_schema: list[Dict[str, Any]] | None,
            observation: str | None
        ) -> str:
            """Generate next action using LLM reasoning."""
            
            system_prompt = """You are an enterprise AI assistant that solves tasks by using tools.

    You will be given:
    1. A task to complete
    2. Available tools with their schemas
    3. An observation from the previous step (if any)

    You must respond with EXACTLY ONE JSON action wrapped in <action>...</action> tags.

    To call a tool:
    <action>
    {
    "type": "tool_call",
    "tool": "tool_name",
    "args": {"arg1": "value1", "arg2": "value2"}
    }
    </action>

    To provide your final answer:
    <action>
    {
    "type": "final_answer",
    "content": "Your comprehensive answer here"
    }
    </action>

    Guidelines:
    - Think step-by-step about what information you need
    - Use tools to gather information before answering
    - Only give final_answer when you have enough information
    - Be precise with tool arguments
    - Do not output anything outside <action>...</action> tags
    """

            tools_text = ""
            if tools_schema:
                tools_text = "\n\nAvailable tools:\n" + json.dumps(
                    {"tools": tools_schema}, indent=2
                )
            
            observation_text = ""
            if observation:
                observation_text = f"\n\nObservation from previous step:\n{observation}"
            
            user_prompt = f"""Task: {task}{tools_text}{observation_text}

    What is your next action?"""

            try:
                
                response = await self._llm.ainvoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
                
                return str(response.content)
            
            except Exception as e:
                print(f"🟣 LLM error: {e}")
                # Fallback: return error as final answer
                return """<action>
    {
    "type": "final_answer",
    "content": "I encountered an error while processing this task."
    }
    </action>"""
    
    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Execute the agent's reasoning loop."""
        input_text = get_message_text(message)
        
        print(f"🟣 Purple agent received: {input_text[:200]}...")
        self._llm = self._get_llm()
        # Extract task information from the prompt
        if "<task>" in input_text:
            task_match = re.search(r"<task>(.*?)</task>", input_text, re.DOTALL)
            task = task_match.group(1).strip() if task_match else ""
        else:
            task = input_text
        
        # Extract tools schema
        tools_match = re.search(
            r"<tools_schema_json>(.*?)</tools_schema_json>",
            input_text,
            re.DOTALL
        )
        tools_schema = None
        if tools_match:
            try:
                tools_data = json.loads(tools_match.group(1))
                tools_schema = tools_data.get("tools", [])
            except json.JSONDecodeError:
                pass
        
        # Extract observation
        obs_match = re.search(r"<observation>(.*?)</observation>", input_text, re.DOTALL)
        observation = obs_match.group(1).strip() if obs_match else None
        
        await updater.update_status(
            TaskState.working,
            new_agent_text_message("🤔 Analyzing task...", context_id=message.context_id)
        )
        
        # Generate action using LLM
        response = await self._generate_action(task, tools_schema, observation)
        
        print(f"🟣 Purple agent responding with: {response[:200]}...")
        
        # Return response wrapped in <action> tags
        await updater.add_artifact(
            parts=[Part(root=TextPart(text=response))],
            name="agent_response"
        )
