# HLD-to-LLD Mapping


## HLD Component

- Name the specific HLD component you are zooming into
- State its responsibility in the overall system in one sentence
- Reference the HLD diagram or phase where it appears


## LLD Scope

- Define exactly what this LLD covers and what it does not
- List the inputs this component receives and the outputs it produces
- Identify the upstream and downstream components it interacts with


## Boundary Decisions

- State what logic lives inside this component vs. what is delegated to other services
- Justify where you drew the boundary (latency, team ownership, deployment independence)
- Note any shared libraries or contracts this component depends on
