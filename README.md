Purple Agent README (EnterprisePlatform-PurpleAgent)

```markdown
# EnterprisePlatform-PurpleAgent 🟣

Baseline purple agent for enterprise task evaluation using MCP tools and Azure OpenAI.

## Overview

EnterprisePlatform-PurpleAgent is a baseline implementation of an enterprise AI agent that:
- Understands task requirements
- Selects appropriate tools from available MCP tools
- Executes tool calls with correct parameters
- Provides clear final answers

This agent serves as a baseline for the EnterprisePlatform benchmark.

## Features

- **Azure OpenAI Integration**: Uses GPT-4o for reasoning
- **Tool Selection**: Intelligently chooses from 69+ enterprise tools
- **Multi-step Planning**: Handles complex workflows
- **Error Handling**: Gracefully manages tool failures
- **A2A Protocol**: Standard agent communication

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/ast-fri/EnterprisePlatform-PurpleAgent.git
cd EnterprisePlatform-PurpleAgent
2. Set Environment Variables
```
```bash
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"
export AZURE_OPENAI_API_VERSION="2024-02-01"
```
3. Build and Run
```bash
# Build Docker image
docker build -t ghcr.io/ast-fri/enterpriseplatform-purpleagent:latest .

# Run agent
docker run -p 9009:9009 \
  -e AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY \
  -e AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
  ghcr.io/ast-fri/enterpriseplatform-purpleagent:latest
```
How It Works
1. Receives Task Prompt
xml
<task_query>Send a Hi message to suraj.nagaje</task_query>
<tools_schema_json>
{
  "tools": [
    {
      "name": "send_direct_message",
      "description": "Send DM to user",
      "parameters": {...}
    }
  ]
}
</tools_schema_json>
2. Reasons About Solution
The agent uses Azure OpenAI to:

Understand the task requirement

Identify relevant tools

Plan the execution strategy

3. Executes Action
Returns structured action:

json
{
  "type": "tool_call",
  "tool": "send_direct_message",
  "args": {
    "username": "suraj.nagaje",
    "message": "Hi"
  }
}
4. Provides Final Answer
After receiving tool result:

json
{
  "type": "final_answer",
  "content": "Message 'Hi' sent successfully to @suraj.nagaje"
}
Configuration
Environment Variables
Variable	Description	Required
AZURE_OPENAI_API_KEY	Azure OpenAI API key	Yes
AZURE_OPENAI_ENDPOINT	Azure OpenAI endpoint	Yes
AZURE_OPENAI_DEPLOYMENT	Model name (default: gpt-4o)	No
AZURE_OPENAI_API_VERSION	API version	No
MAX_TOKENS	Max tokens per response	No
TEMPERATURE	Sampling temperature	No
Message Protocol
Input Format
The agent expects messages in this format:

text
You are an enterprise assistant.

You have access to these tools:
<tools_schema_json>
{...}
</tools_schema_json>

Task: <task_query>

Previous observation (if any): <observation>

Respond with action in XML:
<action>
{"type": "tool_call", "tool": "...", "args": {...}}
</action>
Output Format
xml
<action>
{
  "type": "tool_call" | "final_answer",
  "tool": "tool_name",  // if tool_call
  "args": {...},        // if tool_call
  "content": "..."      // if final_answer
}
</action>
Evaluation
Submit your agent to the leaderboard:

```bash
# Fork the leaderboard repo
gh repo fork ast-fri/EnterprisePlatform-leaderboard
```
# Update scenario.toml with your agent
[[participants]]
role = "YourAgent"
endpoint = "http://your-agent:9009"
image = "ghcr.io/your-org/your-agent:latest"

# Push and create PR
git add scenario.toml
git commit -m "Submit: YourAgent"
git push
Improving the Baseline
To create a better agent:

Better Prompting: Improve system prompts and few-shot examples

Tool Selection: Add reasoning about tool relevance

Error Recovery: Handle tool failures more gracefully

Multi-step Planning: Better planning for complex tasks

Context Management: Track conversation history

Development
Project Structure
text
EnterprisePlatform-PurpleAgent/
├── src/
│   ├── agent.py          # Agent logic
│   ├── server.py         # A2A server
│   └── llm.py           # LLM integration
├── Dockerfile
├── pyproject.toml
└── README.md
Local Development
bash
# Install dependencies
uv sync

# Run agent locally
uv run src/server.py --host 0.0.0.0 --port 9009

# Test with curl
curl -X POST http://localhost:9009 \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
Benchmarking Results
Latest results on EnterprisePlatform benchmark:

Metric	Score
Overall	1.00
Tool Use	1.00
Answer Quality	1.00
Success Rate	100%
Avg Time	6.13s
See full results at: 
https://github.com/ast-fri/EnterprisePlatform-leaderboard

Troubleshooting
Agent Not Responding
Check:

Azure OpenAI credentials are correct

API has sufficient quota

Deployment name matches your setup

Tool Calls Failing
Verify:

Tool schema is being parsed correctly

Arguments match expected format

LLM is generating valid JSON

Poor Performance
Try:

Adjusting temperature (lower = more deterministic)

Adding examples to prompts

Using a more capable model

Contributing
Contributions welcome! Please:

Follow existing code style

Add tests for new features

Update documentation

Submit PR with clear description

License
MIT License