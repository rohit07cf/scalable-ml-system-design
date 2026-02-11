# Platform Architecture

## What This Section Covers

- Config-driven LLM platforms: decoupling model logic from application logic
- Gateway and routing patterns for multi-model LLM serving
- Embedding pipelines and index refresh strategies at scale
- Vector databases and feature stores as shared ML infrastructure


## What Interviewers Usually Test

- Can you design shared infrastructure that multiple ML teams consume?
- Do you understand the operational cost of keeping indexes and features fresh?
- Can you articulate why a gateway layer matters and what it routes on?


## Suggested Study Order

1. design_config_driven_llm_platform
2. design_llm_gateway_routing
3. design_embedding_pipeline_index_refresh
4. design_vector_db_system
5. design_feature_store_personalization


## Fast Revision Path

- Re-read "must explain in interview" bullets in each subfolder
- Sketch the data flow from raw document to queryable vector index from memory
- Walk through one gateway routing decision end-to-end (e.g., cost vs latency)
