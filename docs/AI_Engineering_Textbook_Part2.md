# 🧠 AI Engineering Textbook — Part 2: NLP, Tokenizers, Embeddings & Transformers

---

## CHAPTER 3: Natural Language Processing (NLP)

---

### 3.1 What is NLP?

**🎤 Interview Answer:**
Natural Language Processing (NLP) is the subfield of AI concerned with enabling machines to understand, interpret, and generate human language. It spans tasks including text classification, named entity recognition (NER), machine translation, question answering, and text generation. Modern NLP is dominated by transformer-based pre-trained language models.

**👶 Simple Explanation:**
NLP teaches computers to understand human language — not just find keywords, but understand *meaning*. "I'm feeling blue" doesn't mean someone is painted blue. NLP helps computers figure out what you *actually* mean. It's behind autocomplete, chatbots, and Google Translate.

**Core NLP Tasks:**
| Task | Example |
|------|---------|
| Text Classification | Is this email spam or not? |
| Named Entity Recognition | "Apple" = company, "Tim Cook" = person |
| Sentiment Analysis | Is this review positive or negative? |
| Machine Translation | English → French |
| Question Answering | "Who invented the telephone?" → "Alexander Graham Bell" |
| Text Summarization | 10-page article → 3 sentences |
| Text Generation | Write the next sentence given a prompt |

---

### 3.2 Tokenizers

**🎤 Interview Answer:**
Tokenization is the process of converting raw text into discrete units (tokens) that a model can process. Modern tokenizers use subword segmentation algorithms like Byte-Pair Encoding (BPE) or WordPiece, which balance vocabulary size with the ability to handle out-of-vocabulary words. Each token is mapped to a unique integer ID, which is then converted to an embedding vector.

**👶 Simple Explanation:**
Computers can't read text. They only understand numbers. A tokenizer splits your sentence into pieces (tokens) and maps each piece to a number. Then the model works with those numbers.

```
"Hello, how are you?"
↓ tokenize
["Hello", ",", "how", "are", "you", "?"]
↓ map to IDs
[7592, 1010, 2129, 2024, 2017, 1029]
```

**Types of Tokenization:**
| Method | Description | Example |
|--------|-------------|---------|
| **Word-level** | Split by spaces | "playing" → ["playing"] |
| **Character-level** | Each character is a token | "cat" → ["c","a","t"] |
| **Subword (BPE)** | Split rare words into pieces | "unhappiness" → ["un","happi","ness"] |
| **WordPiece** | Used by BERT | "running" → ["run","##ning"] |
| **SentencePiece** | Used by T5, LLaMA | Language-agnostic subwords |

```python
from transformers import AutoTokenizer

# BERT Tokenizer (WordPiece)
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

text = "Tokenization is fascinating!"
tokens = tokenizer.tokenize(text)
ids    = tokenizer.encode(text)

print("Tokens:", tokens)
# ['token', '##ization', 'is', 'fascinating', '!']
print("IDs:", ids)
# [101, 19204, 3989, 2003, 17237, 999, 102]
# 101 = [CLS], 102 = [SEP] (special BERT tokens)

# Decode back
decoded = tokenizer.decode(ids)
print("Decoded:", decoded)  # [CLS] tokenization is fascinating! [SEP]

# GPT-2 Tokenizer (BPE)
gpt_tokenizer = AutoTokenizer.from_pretrained("gpt2")
gpt_tokens = gpt_tokenizer.tokenize("Hello, world!")
print("GPT tokens:", gpt_tokens)  # ['Hello', ',', 'Ġworld', '!']
```

**Special Tokens:**
| Token | Token Name | Purpose |
|-------|-----------|---------|
| `[CLS]` | Classification | BERT: start of sequence |
| `[SEP]` | Separator | BERT: separate two sentences |
| `[PAD]` | Padding | Make all sequences same length |
| `[MASK]` | Mask | BERT masking for training |
| `<s>` | Start | LLaMA/GPT: beginning of text |
| `</s>` | End | End of sequence signal |

---

### 3.3 Embeddings

**🎤 Interview Answer:**
Embeddings are dense vector representations of discrete tokens (words, sentences, or documents) in a continuous high-dimensional space (typically 128–4096 dimensions). They encode semantic meaning such that semantically similar items appear closer together in vector space. Embeddings are learned during pre-training and capture rich linguistic relationships.

**👶 Simple Explanation:**
Words can't be fed to neural networks directly. We convert each word into a list of 768 numbers (for BERT). The magic? Words with similar meanings get similar number lists!

```
"King"   → [0.2, 0.8, 0.1, 0.9, ...]  (768 numbers)
"Queen"  → [0.2, 0.8, 0.1, 0.7, ...]  (very similar!)
"Banana" → [0.9, 0.1, 0.8, 0.2, ...]  (very different)
```

The famous demo: `King - Man + Woman ≈ Queen` (vector arithmetic works!)

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

sentences = [
    "The cat sat on the mat",
    "A feline rested on the rug",     # Similar meaning
    "I love eating pizza",             # Different topic
]

# Generate embeddings
embeddings = model.encode(sentences)
print(f"Shape: {embeddings.shape}")   # (3, 384) — 384-dim vectors

# Cosine similarity between sentence 0 and 1
from sklearn.metrics.pairwise import cosine_similarity
sim_01 = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
sim_02 = cosine_similarity([embeddings[0]], [embeddings[2]])[0][0]

print(f"Similarity (cat/feline): {sim_01:.3f}")   # ~0.85 (high!)
print(f"Similarity (cat/pizza):  {sim_02:.3f}")   # ~0.12 (low)
```

**Types of Embeddings:**
| Type | Model Examples | Dimensions | Use Case |
|------|---------------|------------|---------|
| Word Embeddings | Word2Vec, GloVe, FastText | 100–300 | Basic NLP |
| Contextualized | BERT, RoBERTa | 768 | Same word, different meanings |
| Sentence | Sentence-BERT, E5 | 384–1024 | Semantic search |
| Document | Doc2Vec, LongFormer | 768+ | Long document retrieval |
| Multimodal | CLIP, ImageBind | 512–1024 | Image+text together |

---

### 3.4 Cosine Similarity

**🎤 Interview Answer:**
Cosine similarity measures the cosine of the angle between two vectors in a high-dimensional space. It ranges from -1 (opposite) to 1 (identical), with 0 indicating orthogonality (no relation). It is preferred over Euclidean distance for high-dimensional embeddings because it is magnitude-invariant — only the direction (meaning) matters, not the length.

**👶 Simple Explanation:**
Imagine two arrows pointing in a room. If they point in the same direction: similarity = 1 (identical meaning). If they're perpendicular: similarity = 0 (unrelated). If opposite directions: similarity = -1.

```
          Cosine Similarity = (A · B) / (||A|| × ||B||)

"I love dogs" and "I adore dogs" → ~0.95 (very similar direction)
"I love dogs" and "quantum physics" → ~0.05 (very different direction)
```

```python
import numpy as np

def cosine_similarity_manual(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    magnitude   = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    return dot_product / magnitude

a = np.array([1, 2, 3])
b = np.array([1, 2, 3])   # Identical
c = np.array([3, 2, 1])   # Different order

print(f"Same vectors: {cosine_similarity_manual(a, b):.3f}")  # 1.000
print(f"Diff vectors: {cosine_similarity_manual(a, c):.3f}")  # 0.714
```

---

### 3.5 Vector Databases

**🎤 Interview Answer:**
A vector database is a specialized storage and retrieval system optimized for high-dimensional embedding vectors. Unlike traditional SQL databases that search by exact match or range queries, vector databases perform Approximate Nearest Neighbor (ANN) search using indexing algorithms like HNSW or IVF to find the most semantically similar vectors to a query — at millisecond latency for millions of vectors.

**👶 Simple Explanation:**
Imagine you have 10 million documents and their embeddings. When a user asks a question, you convert the question to an embedding and need to find the most similar documents. You can't compare to all 10 million one-by-one — too slow! A vector database has smart indexing that finds the closest matches in milliseconds.

```
Normal Database:  SELECT * WHERE name = 'John'      (exact match)
Vector Database:  FIND 5 closest to this embedding  (semantic match)
```

**Popular Vector Databases:**
| Database | Type | Best For | Notes |
|----------|------|---------|-------|
| **FAISS** | Library (Meta) | Research, fast prototyping | In-memory, no GUI |
| **Pinecone** | Cloud SaaS | Production apps | Fully managed |
| **Weaviate** | Open Source | Production + hybrid search | Has schema |
| **Qdrant** | Open Source | Production, Rust-based | Fast, filterable |
| **ChromaDB** | Open Source | Local dev, RAG projects | Easy setup |
| **Milvus** | Open Source | Large-scale enterprise | Kubernetes-native |
| **pgvector** | PostgreSQL ext | Existing Postgres users | SQL + vectors |

```python
# ChromaDB Example (easiest to start with)
import chromadb

client = chromadb.Client()
collection = client.create_collection("my_docs")

# Add documents with embeddings
collection.add(
    documents=["The sky is blue", "Python is great", "AI is transforming tech"],
    ids=["doc1", "doc2", "doc3"]
)

# Query — find most similar
results = collection.query(
    query_texts=["What color is the sky?"],
    n_results=2
)
print(results['documents'])
# [['The sky is blue', 'AI is transforming tech']]
```

---

### 3.6 FAISS — Facebook AI Similarity Search

**🎤 Interview Answer:**
FAISS is a library developed by Meta AI for efficient similarity search over dense vectors. It implements multiple index types with different speed/accuracy tradeoffs: `IndexFlatL2` (exact, slow), `IndexIVFFlat` (approximate, faster), and `IndexHNSWFlat` (graph-based, fastest for large datasets). FAISS supports both CPU and GPU execution.

**👶 Simple Explanation:**
FAISS is the engine that powers many vector databases. If ChromaDB is a car, FAISS is the engine inside it. It's incredibly fast at finding "nearest neighbors" — the most similar vectors to your query. It's free and open-source from Meta.

```python
import faiss
import numpy as np

# Create 10,000 vectors of dimension 128
dimension = 128
num_vectors = 10000

# Random database of embeddings
db_vectors = np.random.randn(num_vectors, dimension).astype('float32')

# Build FAISS index (L2 = Euclidean distance)
index = faiss.IndexFlatL2(dimension)
index.add(db_vectors)
print(f"Indexed {index.ntotal} vectors")

# Search: find 5 nearest neighbors
query = np.random.randn(1, dimension).astype('float32')
distances, indices = index.search(query, k=5)

print("Nearest indices:", indices)      # IDs of top-5 matches
print("Distances:", distances)          # How far each match is

# For large datasets, use IVF (much faster, slightly less accurate)
quantizer = faiss.IndexFlatL2(dimension)
ivf_index = faiss.IndexIVFFlat(quantizer, dimension, 100)
ivf_index.train(db_vectors)
ivf_index.add(db_vectors)
```

**FAISS Index Types:**
| Index | Speed | Accuracy | Memory |
|-------|-------|----------|--------|
| `IndexFlatL2` | Slow | 100% | High |
| `IndexFlatIP` | Slow | 100% | High |
| `IndexIVFFlat` | Fast | ~95% | Medium |
| `IndexHNSWFlat` | Fastest | ~98% | High |
| `IndexIVFPQ` | Fast | ~90% | Low |

---

### 3.7 Top-K Search

**🎤 Interview Answer:**
Top-K retrieval returns the K most relevant results ranked by similarity score (cosine similarity or dot product). In RAG systems, top-K is a critical hyperparameter: too small and you miss relevant context; too large and you overwhelm the LLM with irrelevant noise, increasing hallucination risk and latency.

**👶 Simple Explanation:**
When you search Google, it doesn't show you one result — it shows the Top 10 most relevant pages. Top-K in vector search is the same idea. K=5 means "give me the 5 most similar document chunks to my question." Too few = missing info. Too many = confusing the AI.

```python
# Top-K with FAISS
k = 5   # Retrieve 5 most similar chunks
D, I = index.search(query_embedding, k=k)

# Top-K with Sentence Transformers
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

corpus = [
    "Python is popular for data science",
    "Java is used in enterprise",
    "Machine learning uses Python",
    "Deep learning powers modern AI",
    "SQL is used for databases"
]

query = "AI and Python"
corpus_emb = model.encode(corpus, convert_to_tensor=True)
query_emb  = model.encode(query, convert_to_tensor=True)

# Top-K cosine search
hits = util.semantic_search(query_emb, corpus_emb, top_k=3)
for hit in hits[0]:
    print(f"Score: {hit['score']:.3f} — {corpus[hit['corpus_id']]}")
```

---

### 3.8 Transformers Architecture

**🎤 Interview Answer:**
The Transformer is a neural network architecture introduced in "Attention Is All You Need" (Vaswani et al., 2017). It revolutionized NLP by replacing recurrence with self-attention, enabling parallel processing of sequences. Its core mechanism — multi-head self-attention — allows each token to attend to every other token in the sequence, capturing long-range dependencies without recurrence.

**👶 Simple Explanation:**
Before Transformers, RNNs read sentences word-by-word, like reading a book one letter at a time — slow and they forget early words. Transformers read the whole sentence at once and use "attention" to figure out which words are important to each other. "The dog sat on the mat because *it* was tired" — attention helps understand that "it" = "dog."

```
Transformer Architecture (Encoder-Decoder):

Input Text
    ↓
[Token Embeddings] + [Positional Encoding]
    ↓
[Multi-Head Self-Attention]    ← Each token looks at all others
    ↓
[Feed-Forward Network]
    ↓
[Layer Norm + Residual]
    ↓
(Repeat N times)
    ↓
[Output Embeddings / Logits]
```

**Self-Attention Formula:**
```
Attention(Q, K, V) = softmax(QK^T / √d_k) × V

Q = Query  (what am I looking for?)
K = Key    (what do I contain?)
V = Value  (what do I output if you attend to me?)
```

```python
import torch
import torch.nn as nn

class SelfAttention(nn.Module):
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        self.attention = nn.MultiheadAttention(embed_dim, num_heads)
    
    def forward(self, x):
        # x shape: [seq_len, batch, embed_dim]
        attn_out, attn_weights = self.attention(x, x, x)
        return attn_out, attn_weights

# Using PyTorch's built-in Transformer
transformer = nn.Transformer(
    d_model=512,       # Embedding dimension
    nhead=8,           # Number of attention heads
    num_encoder_layers=6,
    num_decoder_layers=6
)
```

**Transformer Variants:**
| Model | Type | Architecture | Use Case |
|-------|------|-------------|---------|
| BERT | Encoder-only | Bidirectional | Understanding, classification |
| GPT | Decoder-only | Causal/unidirectional | Text generation |
| T5 | Encoder-Decoder | Full | Translation, summarization |
| BART | Encoder-Decoder | Denoising | Summarization, correction |
| LLaMA | Decoder-only | Optimized GPT | Open-source LLM |
| Mistral | Decoder-only | Sliding-window attention | Efficient LLM |
| Gemma | Decoder-only | Google | Efficient open LLM |

---

### 3.9 Attention Mechanisms — Deep Dive

**🎤 Interview Answer:**
Multi-Head Attention runs multiple self-attention operations in parallel (each "head"), then concatenates and projects results. This allows the model to jointly attend to information from different representation subspaces — one head might track syntactic relationships while another tracks semantic ones. Modern variants include Flash Attention (memory-efficient), Grouped Query Attention (GQA), and Sliding Window Attention.

**👶 Simple Explanation:**
8 attention heads = 8 different students reading the same sentence and each highlighting different things. Student 1 highlights verbs, Student 2 highlights who does what, Student 3 highlights emotions, etc. You combine all their highlights to get the full picture.

**Modern Attention Variants:**
| Variant | Description | Used By |
|---------|-------------|---------|
| Multi-Head Attention | Original — full attention | BERT, GPT-2 |
| Flash Attention | Memory-efficient exact attention | GPT-4, LLaMA 2+ |
| Grouped Query Attention (GQA) | Fewer key-value heads | LLaMA 2, Mistral |
| Sliding Window Attention | Local window only | Mistral, Longformer |
| Linear Attention | O(n) complexity | Research |

---

### 3.10 Embedding Models — Key Players

**🎤 Interview Answer:**
Embedding models convert text into dense vector representations. The field has evolved from Word2Vec (2013) through BERT contextualized embeddings to modern sentence encoders. State-of-the-art models include OpenAI's text-embedding-3-large, Cohere's embed-v3, and open-source models like E5-large and BGE.

| Model | Dimensions | Provider | Notes |
|-------|-----------|----------|-------|
| `text-embedding-3-small` | 1536 | OpenAI | Cheap, good |
| `text-embedding-3-large` | 3072 | OpenAI | Best quality |
| `all-MiniLM-L6-v2` | 384 | Sentence-BERT | Free, fast |
| `BAAI/bge-large-en-v1.5` | 1024 | BAAI | Open-source SOTA |
| `E5-large-v2` | 1024 | Microsoft | Strong for retrieval |
| `cohere-embed-v3` | 1024 | Cohere | Production ready |
| `CLIP` | 512 | OpenAI | Image+text |

```python
# OpenAI Embeddings
from openai import OpenAI

client = OpenAI()

def get_embedding(text, model="text-embedding-3-small"):
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding

embedding = get_embedding("What is machine learning?")
print(f"Dimension: {len(embedding)}")  # 1536
```

---

*End of Part 2. Continue to Part 3: RAG, LLMs, LangChain & Advanced AI Concepts*
