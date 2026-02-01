from langchain_ollama import ChatOllama
from langchain_core.tools import tool
# Corrected: Import from langchain.agents for AgentExecutor compatibility
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
import psutil
import time
import json

@tool
def get_system_metrics() -> str:
    """Get current CPU, memory, and disk usage metrics."""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics = {
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / (1024**3), 1),
        "memory_total_gb": round(memory.total / (1024**3), 1),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / (1024**3), 1),
        "disk_total_gb": round(disk.total / (1024**3), 1)
    }
    return json.dumps(metrics, indent=2)

@tool  
def analyze_system_health(metrics_json: str) -> str:
    """Analyze system metrics and provide health recommendations. Expects a JSON string input."""
    try:
        # Clean the input in case the LLM included prefixes
        cleaned_input = metrics_json.strip()
        if "Observation:" in cleaned_input:
            cleaned_input = cleaned_input.split("Observation:")[-1].strip()
            
        metrics = json.loads(cleaned_input)
        analysis = []
        
        if metrics["cpu_percent"] > 80:
            analysis.append("?? HIGH CPU usage")
        if metrics["memory_percent"] > 85:
            analysis.append("?? HIGH Memory usage")
        if metrics["disk_percent"] > 90:
            analysis.append("?? CRITICAL Disk space")
        
        return "? HEALTHY" if not analysis else "?? DEGRADED: " + ", ".join(analysis)
    except Exception as e:
        return f"Error: Please provide the exact JSON string from get_system_metrics. (Details: {e})"

# Initialize LLM
llm = ChatOllama(model="llama3.1", temperature=0)
tools = [get_system_metrics, analyze_system_health]

# Fixed Prompt: ReAct agents require a specific structure (Tools, Thought, Action, etc.)
# Using a standard ReAct template from LangChain Hub style
prompt = PromptTemplate.from_template("""
You are an AIOps system monitoring agent. 
Monitor infrastructure health and provide proactive recommendations.

TOOLS:
------
You have access to the following tools:
{tools}

To use a tool, you MUST use the following format:

Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the exact input to the action
Observation: the result of the action

... (this Thought/Action/Action Input/Observation can repeat N times)

When you have a final response, or if you do not need to use a tool, you MUST use the format:

Thought: Do I need to use a tool? No
Final Answer: [your response here]

CRITICAL RULES:
1. When using 'analyze_system_health', the 'Action Input' MUST be the EXACT JSON string received from the 'Observation' of 'get_system_metrics'.
2. Do not explain the JSON or add text like "Observation:" inside the 'Action Input'.

Query: {input}
{agent_scratchpad}
""")

# Create the agent using the LangChain implementation
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def continuous_monitoring():
    print("?? AIOps System Monitor Started (Ctrl+C to stop)")
    while True:
        try:
            print("\n" + "="*60)
            print(f"?? Scan at {time.strftime('%H:%M:%S')}")
            result = agent_executor.invoke({
                "input": "Provide current system metrics and health analysis."
            })
            print("\n?? AIOps Health Report:", result["output"])
            time.sleep(10)  # Scan every 10 seconds
        except KeyboardInterrupt:
            print("\n?? Monitoring stopped by user")
            break
        except Exception as e:
            print(f"? Error during scan: {e}")
            time.sleep(5)

if __name__ == "__main__":
    continuous_monitoring()





    