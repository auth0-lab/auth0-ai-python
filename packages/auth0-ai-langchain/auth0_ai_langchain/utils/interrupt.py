from auth0_ai.interrupts.auth0_interrupt import Auth0Interrupt
from langgraph.errors import GraphInterrupt


def to_graph_interrupt(interrupt: Auth0Interrupt) -> GraphInterrupt:
    return GraphInterrupt([
        {
            "value": interrupt,
            "when": "during",
            "resumable": True,
            "ns": [f"auth0AI:{interrupt.__class__.__name__}:{interrupt.code}"]
        }
    ])
