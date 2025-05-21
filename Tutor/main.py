from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition   
from langgraph.graph.message import add_messages
from IPython.display import Image, display

from Tutor.Services.InputHandler import InputHandler
from Tutor.Tools.OCRModel import ocr_tool

class State(TypedDict):
    messages: Annotated[list, add_messages]


input_handler = InputHandler()
graph_builder = StateGraph(State)
tools = [ocr_tool]

graph_builder.add_node("ocr", ocr_tool)
graph_builder.add_conditional_edges(
        START,
        tools_condition(
            condition=lambda x: input_handler.check_input_type(x) == "image", 
            true_node="ocr",
            false_node=END,
        ),
    )
graph_builder.add_edge("ocr", END)
graph = graph_builder.compile()

# Visualize the graph
print(graph.get_graph().draw_ascii())






