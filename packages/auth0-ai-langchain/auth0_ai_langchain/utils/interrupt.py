from auth0_ai.interrupts.auth0_interrupt import Auth0Interrupt
from langgraph.errors import GraphInterrupt
from langgraph.types import Interrupt

def to_graph_interrupt(interrupt: Auth0Interrupt) -> GraphInterrupt:
    return GraphInterrupt([
        Interrupt(
            value=interrupt.to_json(),
            when="during",
            resumable=True,
            ns=[f"auth0AI:{interrupt.__class__.__name__}:{interrupt.code}"]
        )
    ])
