# Phase 5 -- Database Design


## Data Models

- Define the core entities and their attributes
- Specify primary keys, foreign keys, and unique constraints
- Note which fields are indexed for query performance


## Storage Choices

- Choose the storage engine for each data type (relational, document, key-value, vector, blob)
- Justify each choice with one sentence referencing access pattern or data shape
- Note any polyglot persistence trade-offs


## Indexing Strategy

- List the most frequent query patterns and the indexes that support them
- Consider composite indexes for multi-column lookups
- Note the write amplification cost of each additional index


## Partitioning

- Choose a partition key and justify it based on query distribution
- Estimate the number of partitions and size per partition
- Describe how you handle hot partitions or skewed keys
