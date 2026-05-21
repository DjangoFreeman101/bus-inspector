# Markov Chain — Next Word Predictor

A next-word prediction engine built from scratch in Python, with an interactive Streamlit web interface. No ML libraries, just probability theory and linear algebra.

## Live Demo
[Try it here](https://markovnextwordpredictor-gydrnxmhlpx4ajrkefpzwj.streamlit.app/)

## What it does
- Trains a Markov chain transition matrix on any text corpus you provide
- Predicts the most likely next word(s) in real time as you type
- Supports incremental online learning — add new words without retraining (O(1) update vs O(n) full retrain)
- Visualizes the transition probability matrix as an interactive heatmap
- Adjustable Markov order (1, 2, or 3 words of context)

## Demo

Type any text from your corpus and watch predictions appear instantly:

| Input | Top Predictions |
|---|---|
| `"the"` | president (42%), united (28%), trump (18%) |
| `"donald"` | trump (94%), j (6%) |
| `"united"` | states (100%) |

## How it works

A Markov chain models text as a sequence of states and transitions. Given the current word (or last N words), the model predicts the next word based on transition probabilities learned from the corpus:

$$P(\text{next word} = j \mid \text{current state} = i) = \frac{\text{count}(i \rightarrow j)}{\sum_k \text{count}(i \rightarrow k)}$$

### The pipeline
```
Raw text
   ↓
Preprocessing      → lowercase, clean punctuation, handle contractions
   ↓
Count matrix       → count every (state → next_word) transition
   ↓
Probability matrix → normalize each row to sum to 1.0
   ↓
Predict            → look up current state, return top N by probability
   ↓
Incremental update → O(1) update when new words are added
```

### Incremental learning
The model separates raw counts from probabilities. When a new word arrives, only the single affected row is updated and renormalized — no reprocessing of the full corpus. This is the same principle behind online learning and streaming models in production systems.

## Tech stack
- **Python** — core logic, no ML libraries
- **Streamlit** — web interface
- **Plotly** — interactive heatmap visualization
- **Regex** — text preprocessing

## Run locally

```bash
pip install -r requirements.txt
streamlit run markov_app.py
```

## Project structure
```
markov_next_word_predictor/
├── markov_app.py       # Streamlit app + all engine logic
├── requirements.txt    # dependencies
└── README.md
```

## Concepts demonstrated
- Markov chains and transition matrices
- Online / incremental learning (O(1) updates)
- Probabilistic text modeling
- The statistical foundation that evolved into modern LLMs (n-grams → RNNs → Transformers)

## Context — from Markov chains to LLMs
This project implements the conceptual ancestor of modern language models. Every stage of NLP evolution — n-gram models, RNNs, LSTMs, and Transformers — is solving the same two problems this model has: a fixed memory window and no generalization to unseen words. Understanding Markov chains is understanding where it all started.

## Author
Built as a data science portfolio project.
