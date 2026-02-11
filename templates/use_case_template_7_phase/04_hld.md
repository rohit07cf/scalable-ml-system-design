# Phase 4 -- High-Level Design


## System Context

- Draw the boundary between your system and external actors (users, upstream services, third-party APIs)
- Identify what data enters and leaves the system
- Note which components are in scope for this design


## Core Components

- List each major component (e.g., API gateway, feature store, model server, message queue)
- State the responsibility of each component in one sentence
- Indicate whether each is synchronous or asynchronous


## Data Flow

- Trace the path of a single request from ingestion to response
- Trace the offline path from raw data to trained model to deployment
- Identify where data is transformed, cached, or persisted


## Key Interactions

- Describe the most critical component-to-component interactions
- Note synchronous vs. asynchronous communication patterns
- Highlight where failures would have the most impact
