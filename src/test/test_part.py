import pytest

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

def create_graph() -> StateGraph:
    class MyState(TypedDict):
        my_key: str

    graph = StateGraph(MyState)
    graph.add_node("node1", lambda state: {"my_key": "hello from node1"})
    graph.add_node("node2", lambda state: {"my_key": "hello from node2"})
    graph.add_node("node3", lambda state: {"my_key": "hello from node3"})
    graph.add_node("node4", lambda state: {"my_key": "hello from node4"})
    graph.add_edge(START, "node1")
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", "node3")
    graph.add_edge("node3", "node4")
    graph.add_edge("node4", END)
    return graph

def test_partial_execution_from_node2_to_node3() -> None:
    checkpointer = MemorySaver()
    graph = create_graph()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    compiled_graph.update_state(
        config={
          "configurable": {
            "thread_id": "1"
          }
        },
        # The state passed into node 2 - simulating the state at
        # the end of node 1
        values={"my_key": "initial_value"},
        # Update saved state as if it came from node 1
        # Execution will resume at node 2
        as_node="node1",
    )
    result = compiled_graph.invoke(
        # Resume execution by passing None
        None,
        config={"configurable": {"thread_id": "1"}},
        # Stop after node 3 so that node 4 doesn't run
        interrupt_after="node3",
    )
    assert result["my_key"] == "hello from node3"