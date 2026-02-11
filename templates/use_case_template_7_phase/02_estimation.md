# Phase 2 -- Estimation


## Traffic Estimation

- Estimate daily active users and requests per second (peak and average)
- Break down read vs. write ratio
- Note any seasonal or time-of-day traffic spikes


## Storage Estimation

- Estimate raw data size (features, embeddings, logs) per record
- Project total storage over 1 year and 3 years
- Account for replication factor and backup overhead


## Compute Estimation

- Estimate inference cost per request (CPU vs. GPU, model size)
- Estimate training cost (frequency, dataset size, hardware)
- Factor in preprocessing and feature engineering compute


## Cost Estimation

- Translate compute and storage into approximate monthly cloud cost
- Identify the top cost drivers and where optimization matters most
- Compare build vs. buy for key components (e.g., managed ML platform vs. custom)
