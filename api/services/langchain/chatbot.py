import os
from langchain_openai import ChatOpenAI
from api.services.langchain.models.state import State
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
from PIL import Image as PILImage
import io
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from api.services.langchain.models.BasicToolNode import BasicToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


from langchain_core.tools import tool

load_dotenv()

@tool
def multiply_tool(a: int, b: int) -> int:
    """Multiply two numbers"""
    print('multiply_tool: Called')
    return a * b

@tool
def get_current_status():
    """Get the current status of the system"""
    print('get_current_status: Called')
    return "The system is running smoothly, except on mondays"

tools = [multiply_tool, get_current_status]

print("Initializing chatbot...")
graph_builder = StateGraph(State)
llm = ChatOpenAI(model="gpt-4o-mini")
llm = llm.bind_tools(tools)
def chatbot(state: State) -> State:
    # Convert state.messages to the format expected by the LLM
    # Convert BaseMessage objects to LangChain message objects
    langchain_messages = []
    
    # Add a system message to instruct the LLM about available tools
    system_message = """You have access to the following tools:
1. multiply_tool - Multiply two numbers
2. get_current_status - Get the current status of the system

When a user asks about status or needs to perform calculations, use the appropriate tool. Always use tools when they are relevant to the user's request."""
    langchain_messages.append(SystemMessage(content=system_message))
    
    # Add the existing messages (they're already BaseMessage objects)
    langchain_messages.extend(state.messages)
    
    # Get the LLM response
    response = llm.invoke(langchain_messages)
    
    print(f"DEBUG: Available tools: {[tool.name for tool in tools]}")
    print(f"DEBUG: LLM response content: {response.content[:100]}...")
    
    # Convert back to BaseMessage format for State
    return State(messages=state.messages + [response])

def route_tools(state: State):
    """
    Route to tools if the last message has tool calls, otherwise end.
    """
    if state.messages:
        ai_message = state.messages[-1]
    else:
        raise ValueError(f"No messages found in input state: {state}")
    
    # Check if the message has tool_calls (BaseMessage objects have tool_calls as attribute)
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        print(f"DEBUG: Routing to tools - tool_calls found: {ai_message.tool_calls}")
        return "tools"
    print("DEBUG: No tool calls found, ending")
    return END

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", BasicToolNode(tools=tools))
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {"tools": "tools", END: END}
)
# Loop back from tools to chatbot
graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()
print("Graph compiled successfully!")




# visualize the graph
try:
    # Get the PNG data from the graph
    png_data = graph.get_graph().draw_mermaid_png()
    
    # Convert bytes to PIL Image and save
    pil_image = PILImage.open(io.BytesIO(png_data))
    pil_image.save("graph.png")
    print("Graph saved as graph.png")
except Exception as e:
    print(f"Error saving graph: {e}")


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [HumanMessage(content=user_input)]}):
        state = next(iter(event.values()))
        state_obj = State(**state) if isinstance(state, dict) else state
        last = state_obj.messages[-1]
        if last.content:
            print('Assistant:', last.content)

def test_chatbot():
    while True:

            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            stream_graph_updates(user_input)


    # Remove the problematic get_state() call
    print("Chatbot session completed.")



