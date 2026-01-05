# src/server.py
import argparse
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from executor import Executor


def main():
    parser = argparse.ArgumentParser(description="Run the Baseline Purple Agent")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=9002, help="Port to bind")
    parser.add_argument("--card-url", type=str, help="URL for agent card")
    args = parser.parse_args()

    print("🟣 Starting the Purple Agent (Baseline)")

    skill = AgentSkill(
        id="enterprise_mcp_solver",
        name="Enterprise MCP Task Solver",
        description=(
            "Solves enterprise MCP tasks using ReACT-style reasoning. "
            "Accepts task description and available tools, returns actions or final answers."
        ),
        tags=["purple agent", "solver", "enterprise", "mcp", "ReACT"],
        examples=["""
<task>Send a message to john@example.com saying "Hello"</task>
<tools_schema_json>
{
  "tools": [
    {
      "name": "send_email",
      "description": "Send an email",
      "parameters": {
        "type": "object",
        "properties": {
          "to": {"type": "string"},
          "subject": {"type": "string"},
          "body": {"type": "string"}
        }
      }
    }
  ]
}
</tools_schema_json>
<observation>No previous tool calls have been made yet.</observation>
"""]
    )

    agent_card = AgentCard(
        name="Baseline Purple Agent",
        description="A baseline solver agent for enterprise MCP tasks using ReACT reasoning.",
        url=args.card_url or f"http://{args.host}:{args.port}/",
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill]
    )

    request_handler = DefaultRequestHandler(
        agent_executor=Executor(),
        task_store=InMemoryTaskStore(),
    )
    
    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    
    starlette_app = app.build()
    
    print(f"✅ Agent Card URL: {agent_card.url}")
    print(f"✅ Server starting on http://{args.host}:{args.port}")
    print(f"✅ Agent Card endpoint: http://{args.host}:{args.port}/.well-known/agent-card.json")
    print()
    
    uvicorn.run(starlette_app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
