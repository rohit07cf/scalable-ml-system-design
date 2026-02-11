# Eval Metrics Checklist

Key evaluation metrics to mention in ML system design interviews, organized by task type.


## Classification

- [ ] Precision, recall, and F1 score (especially for imbalanced classes)
- [ ] AUC-ROC for threshold-independent evaluation
- [ ] Log loss for calibration quality
- [ ] Confusion matrix analysis for error type breakdown


## NLP / LLM

- [ ] BLEU, ROUGE, or METEOR for generation quality
- [ ] Perplexity for language model quality
- [ ] Faithfulness and groundedness scores for RAG systems
- [ ] Human evaluation (relevance, fluency, safety) as the gold standard


## Retrieval

- [ ] Precision@k and Recall@k for top-k result quality
- [ ] Mean Reciprocal Rank (MRR) for ranking effectiveness
- [ ] Normalized Discounted Cumulative Gain (NDCG) for graded relevance
- [ ] Latency per query as a practical retrieval performance metric


## Recommendation

- [ ] Hit rate and coverage across the item catalog
- [ ] Mean Average Precision (MAP) for ranked recommendation lists
- [ ] Diversity and novelty metrics to avoid filter bubbles
- [ ] Online metrics: click-through rate, conversion rate, session length
