# test_purple_agent.py
import asyncio
import httpx
from uuid import uuid4

from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, TextPart, Role
from a2a.utils import get_text_parts


async def test_purple_agent():
    """Test the purple agent with various tasks."""
    
    print("="*60)
    print("Testing Purple Agent")
    print("="*60 + "\n")
    
    # Connect to purple agent
    async with httpx.AsyncClient(timeout=60) as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url="http://127.0.0.1:9002"
        )
        
        try:
            agent_card = await resolver.get_agent_card()
            print(f"✅ Connected to: {agent_card.name}")
            print(f"   URL: {agent_card.url}")
            print(f"   Skills: {[s.name for s in agent_card.skills]}\n")
        except Exception as e:
            print(f"❌ Failed to connect to purple agent: {e}")
            print("   Make sure the agent is running: python -m src.server --host 127.0.0.1 --port 9002")
            return
        
        # Create client
        config = ClientConfig(httpx_client=httpx_client, streaming=False)
        factory = ClientFactory(config)
        client = factory.create(agent_card)
        
        # Test cases
        test_cases = [
            {
                "name": "Simple Task with No Tools",
                "task": "Say hello to the user",
                "tools": [],
                "observation": "No previous actions taken."
            },
            {
                "name": "Email Task",
                "task": "Send an email to john@example.com with subject 'Meeting' and body 'Let's meet tomorrow'",
                "tools": [
                    {
                        "name": "send_email",
                        "description": "Send an email to a recipient",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "to": {
                                    "type": "string",
                                    "description": "Email recipient"
                                },
                                "subject": {
                                    "type": "string",
                                    "description": "Email subject"
                                },
                                "body": {
                                    "type": "string",
                                    "description": "Email body text"
                                }
                            },
                            "required": ["to", "subject", "body"]
                        }
                    }
                ],
                "observation": "No previous tool calls have been made yet."
            },
            {
                "name": "Slack Message Task",
                "task": "Send a message 'Project update ready' to the #engineering channel",
                "tools": [
                    {
                        "name": "slack_send_message",
                        "description": "Send a message to a Slack channel",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "channel": {
                                    "type": "string",
                                    "description": "Channel name (e.g., #engineering)"
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Message text to send"
                                }
                            },
                            "required": ["channel", "message"]
                        }
                    }
                ],
                "observation": "No previous tool calls have been made yet."
            },
            {
                "name": "Multi-step Task with Observation",
                "task": "Send an email to jane@example.com thanking her for the report",
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
                            },
                            "required": ["to", "subject", "body"]
                        }
                    }
                ],
                "observation": "Previous action: Attempted to send email but recipient was not found. Need to try again with correct email."
            }
        ]
        
        # Run test cases
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"Test {i}/{len(test_cases)}: {test_case['name']}")
            print(f"{'='*60}")
            
            # Format message
            tools_json = {
                "tools": test_case["tools"]
            }
            import json
            
            message_text = f"""<task>{test_case['task']}</task>
<tools_schema_json>
{json.dumps(tools_json, indent=2)}
</tools_schema_json>
<observation>{test_case['observation']}</observation>"""
            
            print(f"\n📤 Sending task: {test_case['task']}")
            print(f"   Tools available: {len(test_case['tools'])}")
            
            # Send message
            message = Message(
                kind="message",
                role=Role.user,
                parts=[Part(TextPart(kind="text", text=message_text))],
                message_id=uuid4().hex,
            )
            
            try:
                async for event in client.send_message(message):
                    if isinstance(event, tuple):
                        task, _ = event
                        
                        print(f"\n📨 Status: {task.status.state.value}")
                        
                        # Print artifacts (agent response)
                        if task.artifacts:
                            for artifact in task.artifacts:
                                print(f"\n📦 Response:")
                                for part in artifact.parts:
                                    if hasattr(part.root, 'text'):
                                        response_text = part.root.text
                                        print(f"{response_text}\n")
                                        
                                        # Try to parse action
                                        import re
                                        action_match = re.search(r'<action>(.*?)</action>', response_text, re.DOTALL)
                                        if action_match:
                                            try:
                                                action_json = json.loads(action_match.group(1))
                                                print(f"✅ Parsed Action:")
                                                print(f"   Type: {action_json.get('type')}")
                                                if action_json.get('type') == 'tool_call':
                                                    print(f"   Tool: {action_json.get('tool_name')}")
                                                    print(f"   Arguments: {json.dumps(action_json.get('arguments', {}), indent=6)}")
                                                elif action_json.get('type') == 'final_answer':
                                                    print(f"   Answer: {action_json.get('content')}")
                                            except json.JSONDecodeError:
                                                print("⚠️  Could not parse action JSON")
                        
                        # Print status messages
                        if task.status.message:
                            status_text = '\n'.join(get_text_parts(task.status.message.parts))
                            if status_text and status_text != "🟣 Thinking...":
                                print(f"Status: {status_text}")
                
                print(f"\n✅ Test {i} completed")
                
            except Exception as e:
                print(f"\n❌ Test {i} failed: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*60}")
        print("All tests completed!")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_purple_agent())
