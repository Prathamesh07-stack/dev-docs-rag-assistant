# 🧠 AI Engineering Textbook — Part 4: Model Architecture Design & Interview Q&A

---

## CHAPTER 7: How to Train & Build an AI System — Full Architecture Walkthrough

> **The Big Interview Question:** *"Walk me through how you would design and train an AI model for a real problem."*

This chapter walks through a **complete, real-world example**: Building a **Document Intelligence Chatbot** that can answer questions over a company's internal knowledge base.

---

### 7.1 The Problem Statement

**Setting:** A law firm has 50,000 legal documents (contracts, case files, regulations). Lawyers spend hours manually searching. We want a chatbot that answers: *"What are the termination clauses in the ACME contract?"*

**Solution Architecture:** RAG-powered chatbot using:
- Embedding model for document indexing
- Vector database for semantic search
- LLM for answer generation
- LangGraph for orchestration

---

### 7.2 The Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    OFFLINE INDEXING PIPELINE                 │
│                                                             │
│   [PDF/DOCX] → [Text Extract] → [Clean] → [Chunk]          │
│       ↓                                         ↓           │
│   [Embed via OpenAI/BGE]  ←─────────────────────┘          │
│       ↓                                                     │
│   [Store in Vector DB (Pinecone/ChromaDB)]                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    ONLINE INFERENCE PIPELINE                 │
│                                                             │
│  User Question                                              │
│      ↓                                                      │
│  [Query Rewriting] (optional — LLM improves the question)   │
│      ↓                                                      │
│  [Embed Query] → same embedding model used for indexing     │
│      ↓                                                      │
│  [Hybrid Search] → Vector (semantic) + BM25 (keyword)       │
│      ↓                                                      │
│  [Re-Ranking] (Cross-encoder for better relevance)          │
│      ↓                                                      │
│  Top-K Most Relevant Chunks                                 │
│      ↓                                                      │
│  [Prompt Builder] → "You are a legal expert. Context: {chunks} Answer: {question}"
│      ↓                                                      │
│  [LLM (GPT-4o / Claude)] → Generate Answer                 │
│      ↓                                                      │
│  [Citation Injector] → Add source references               │
│      ↓                                                      │
│  Final Response to User                                     │
└─────────────────────────────────────────────────────────────┘
```

---

### 7.3 Step-by-Step Implementation

#### Step 1: Data Collection & Preprocessing

```python
import os
from pathlib import Path
from langchain_community.document_loaders import (
    PyPDFLoader, 
    UnstructuredWordDocumentLoader,
    DirectoryLoader
)

def load_documents(data_dir: str):
    """Load all PDFs and Word docs from a directory."""
    loaders = {
        "**/*.pdf":  PyPDFLoader,
        "**/*.docx": UnstructuredWordDocumentLoader,
    }
    
    all_docs = []
    for pattern, loader_cls in loaders.items():
        loader = DirectoryLoader(data_dir, glob=pattern, loader_cls=loader_cls)
        docs = loader.load()
        all_docs.extend(docs)
    
    print(f"Loaded {len(all_docs)} documents")
    return all_docs

docs = load_documents("./legal_documents/")
```

#### Step 2: Data Cleaning

```python
import re

def clean_text(text: str) -> str:
    """Remove noise from extracted text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove page numbers like "Page 1 of 10"
    text = re.sub(r'Page \d+ of \d+', '', text)
    
    # Remove headers/footers (common in legal docs)
    text = re.sub(r'CONFIDENTIAL.*?\n', '', text)
    
    return text.strip()

for doc in docs:
    doc.page_content = clean_text(doc.page_content)
```

#### Step 3: Smart Chunking

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

def create_chunks(documents, chunk_size=1000, chunk_overlap=200):
    """
    Split documents into chunks.
    
    chunk_size=1000:  ~750 words per chunk — fits embedding context well
    chunk_overlap=200: Prevents cutting mid-sentence context
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )
    
    chunks = splitter.split_documents(documents)
    
    # Add metadata to each chunk for citation
    for i, chunk in enumerate(chunks):
        chunk.metadata['chunk_id'] = i
        chunk.metadata['char_count'] = len(chunk.page_content)
    
    print(f"Created {len(chunks)} chunks from {len(documents)} documents")
    return chunks

chunks = create_chunks(docs)
```

#### Step 4: Embedding & Indexing

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb

def create_vector_store(chunks, persist_dir="./chroma_db"):
    """Embed all chunks and store in ChromaDB."""
    
    # Choose embedding model
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",  # Best OpenAI embedding
        dimensions=1536  # Can reduce to 256 for speed
    )
    
    # Create vector store (this calls the embedding API for all chunks)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="legal_docs"
    )
    
    print(f"Indexed {vectorstore._collection.count()} chunks")
    return vectorstore

vectorstore = create_vector_store(chunks)
```

#### Step 5: Advanced Retrieval

```python
from langchain.retrievers import EnsembleRetriever, BM25Retriever

def create_hybrid_retriever(vectorstore, chunks, k=5):
    """
    Hybrid search = Vector search + BM25 keyword search.
    Vector finds semantically similar content.
    BM25 catches exact keyword matches (important for legal terms, names).
    """
    
    # Dense vector retriever
    vector_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )
    
    # Sparse BM25 retriever
    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = k
    
    # Combine with equal weights
    hybrid_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[0.6, 0.4]  # Slightly favor semantic search
    )
    
    return hybrid_retriever

retriever = create_hybrid_retriever(vectorstore, chunks)
```

#### Step 6: Prompt Engineering

```python
from langchain_core.prompts import ChatPromptTemplate

# Well-engineered system prompt
SYSTEM_PROMPT = """You are an expert legal assistant with 20 years of experience 
analyzing contracts and legal documents.

INSTRUCTIONS:
1. Answer ONLY based on the provided context documents
2. If the answer is not found in the context, say "I cannot find this information in the provided documents"
3. Always cite which document/section your answer comes from
4. Use legal terminology appropriately
5. Be precise — legal accuracy matters

CONTEXT DOCUMENTS:
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{question}"),
])
```

#### Step 7: LangGraph Orchestration

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
import operator

class RAGState(TypedDict):
    question: str
    original_question: str
    documents: List[str]
    answer: str
    needs_clarification: bool
    iteration: int

llm = ChatOpenAI(model="gpt-4o", temperature=0)

def rewrite_query(state: RAGState) -> RAGState:
    """Make the query better for retrieval."""
    rewrite_prompt = f"""Rewrite this question to be more specific and retrieve better legal documents:
    Original: {state['question']}
    Rewritten:"""
    
    better_query = llm.invoke(rewrite_prompt)
    state['question'] = better_query.content
    return state

def retrieve(state: RAGState) -> RAGState:
    """Retrieve relevant document chunks."""
    docs = retriever.invoke(state['question'])
    state['documents'] = [doc.page_content for doc in docs]
    return state

def generate(state: RAGState) -> RAGState:
    """Generate answer from retrieved context."""
    context = "\n\n---\n\n".join(state['documents'])
    
    messages = prompt.format_messages(
        context=context,
        question=state['original_question']
    )
    
    response = llm.invoke(messages)
    state['answer'] = response.content
    return state

def check_answer_quality(state: RAGState) -> RAGState:
    """Self-evaluate if the answer is good."""
    eval_prompt = f"""Is this answer complete and accurate based on the context?
    Question: {state['original_question']}
    Answer: {state['answer']}
    Context available: {len(state['documents'])} chunks
    
    Reply with GOOD if answer is complete, or BAD if we need better retrieval."""
    
    eval = llm.invoke(eval_prompt)
    state['needs_clarification'] = "BAD" in eval.content.upper()
    state['iteration'] = state.get('iteration', 0) + 1
    return state

def route(state: RAGState) -> str:
    """Decide next step."""
    if state.get('needs_clarification') and state.get('iteration', 0) < 2:
        return "rewrite"  # Try again with better query
    return "end"

# Build the graph
graph = StateGraph(RAGState)
graph.add_node("rewrite",  rewrite_query)
graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)
graph.add_node("evaluate", check_answer_quality)

graph.set_entry_point("rewrite")
graph.add_edge("rewrite",  "retrieve")
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", "evaluate")
graph.add_conditional_edges("evaluate", route, 
                             {"rewrite": "rewrite", "end": END})

rag_app = graph.compile()

# Run it
result = rag_app.invoke({
    "question": "What are the termination clauses?",
    "original_question": "What are the termination clauses?",
    "documents": [],
    "answer": "",
    "needs_clarification": False,
    "iteration": 0
})

print(result["answer"])
```

#### Step 8: Evaluation

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,          # Is the answer grounded in context? (no hallucination)
    answer_relevancy,      # Does answer address the question?
    context_precision,     # Are retrieved docs relevant?
    context_recall         # Do retrieved docs contain the answer?
)

from datasets import Dataset

# Prepare evaluation data
eval_data = {
    "question":   ["What are termination clauses?"],
    "answer":     [result["answer"]],
    "contexts":   [result["documents"]],
    "ground_truth": ["The contract may be terminated by either party..."]  # Reference answer
}

dataset = Dataset.from_dict(eval_data)
scores = evaluate(dataset, metrics=[faithfulness, answer_relevancy, 
                                     context_precision, context_recall])
print(scores)
# faithfulness: 0.92  (92% of answer grounded in retrieved context)
# answer_relevancy: 0.88
# context_precision: 0.85
# context_recall: 0.91
```

---

### 7.4 Alternative: Training a Custom Model (from Scratch)

> This is for understanding. In production, you almost always fine-tune rather than train from scratch.

**When to train from scratch?**
- Unique domain with no existing pre-trained models
- Data is proprietary and you can't use external APIs
- You need full control of the architecture

**Training Pipeline for a Custom Text Classifier:**

```python
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
import wandb  # Experiment tracking

# 1. Custom Dataset
class TextDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        return {
            'input_ids':      encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'label':          torch.tensor(self.labels[idx], dtype=torch.long)
        }

# 2. Custom Model (BERT + Classification Head)
class LegalClassifier(nn.Module):
    def __init__(self, num_classes=5):
        super().__init__()
        from transformers import AutoModel
        self.bert = AutoModel.from_pretrained('bert-base-uncased')
        self.dropout = nn.Dropout(0.3)
        self.classifier = nn.Linear(768, num_classes)
    
    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        dropped = self.dropout(pooled)
        logits = self.classifier(dropped)
        return logits

# 3. Training Loop with Best Practices
def train(model, dataloader, optimizer, scheduler, device, epoch):
    model.train()
    total_loss = 0
    criterion = nn.CrossEntropyLoss()
    
    for batch_idx, batch in enumerate(dataloader):
        input_ids      = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels         = batch['label'].to(device)
        
        # Forward
        logits = model(input_ids, attention_mask)
        loss   = criterion(logits, labels)
        
        # Backward
        optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping (prevents exploding gradients)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        scheduler.step()
        
        total_loss += loss.item()
        
        if batch_idx % 50 == 0:
            print(f"Epoch {epoch} | Batch {batch_idx} | Loss: {loss.item():.4f}")
    
    return total_loss / len(dataloader)

# 4. Full Training Script
def full_training_pipeline():
    # Config
    EPOCHS      = 10
    BATCH_SIZE  = 16
    LR          = 2e-5      # Fine-tuning LR for BERT
    MAX_LEN     = 256
    NUM_CLASSES = 5
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Data (replace with your actual data)
    texts  = ["Sample legal text..."] * 100
    labels = [0] * 100
    
    tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
    dataset   = TextDataset(texts, labels, tokenizer, MAX_LEN)
    
    train_size = int(0.8 * len(dataset))
    val_size   = len(dataset) - train_size
    train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE)
    
    # Model
    model = LegalClassifier(num_classes=NUM_CLASSES).to(device)
    
    # Optimizer (AdamW for transformers)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    
    # Learning rate scheduler (warmup then decay)
    total_steps = len(train_loader) * EPOCHS
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=LR, total_steps=total_steps
    )
    
    # Track experiments
    # wandb.init(project="legal-classifier", config={...})
    
    best_val_loss = float('inf')
    
    for epoch in range(1, EPOCHS + 1):
        train_loss = train(model, train_loader, optimizer, scheduler, device, epoch)
        
        # Validation
        model.eval()
        val_loss = 0
        correct  = 0
        with torch.no_grad():
            for batch in val_loader:
                input_ids      = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels         = batch['label'].to(device)
                
                logits = model(input_ids, attention_mask)
                loss   = nn.CrossEntropyLoss()(logits, labels)
                val_loss += loss.item()
                
                preds = logits.argmax(dim=-1)
                correct += (preds == labels).sum().item()
        
        val_accuracy = correct / len(val_ds)
        avg_val_loss = val_loss / len(val_loader)
        
        print(f"Epoch {epoch}: Train Loss={train_loss:.4f}, Val Loss={avg_val_loss:.4f}, Acc={val_accuracy:.4f}")
        
        # Save best model
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), 'best_model.pth')
            print("✅ Saved best model!")

full_training_pipeline()
```

---

### 7.5 Common AI Architecture Patterns — Cheat Sheet

| Pattern | When to Use | Components |
|---------|-------------|-----------|
| **RAG** | Domain-specific Q&A, private data | Embeddings + VectorDB + LLM |
| **Fine-tuning** | Consistent style/domain, few-shot tasks | Pre-trained model + PEFT/LoRA |
| **Prompt Engineering** | Fast iteration, no training needed | LLM + prompt |
| **Agentic AI** | Multi-step tasks, tool use | LLM + Tools + LangGraph |
| **Classification** | Labeling, routing, detection | BERT + classification head |
| **Generative** | Creative, open-ended tasks | GPT-style decoder |
| **Multimodal** | Images + text | CLIP, LLaVA, GPT-4V |

---

## CHAPTER 8: The AI Engineer's Interview Cheat Sheet

---

### 8.1 Quick-Fire Questions & Answers

**Q: What is the difference between AI, ML, and DL?**
> AI is the broad field of making machines intelligent. ML is a subset where machines learn from data instead of explicit rules. DL is a subset of ML using neural networks with many layers.

**Q: What is overfitting and how do you prevent it?**
> Overfitting is when a model memorizes training data but fails on new data. Prevent with: dropout, L2 regularization (weight decay), early stopping, more training data, data augmentation, cross-validation.

**Q: What is the vanishing gradient problem?**
> In deep networks, gradients become exponentially small during backpropagation through many layers, making early layers learn extremely slowly. Solutions: ReLU activations, batch normalization, residual connections (ResNets), LSTMs (for sequences).

**Q: Explain attention in transformers.**
> Attention allows each token to "attend to" (weight the importance of) every other token. For each query token, we compute similarity scores with all key tokens, softmax normalize them, and use them to weighted-sum the value vectors. This captures which words are most relevant to each other.

**Q: What is RAG vs Fine-tuning?**
> RAG retrieves relevant information at inference time — good for dynamic/private data and when you want to cite sources. Fine-tuning bakes knowledge into model weights at training time — better for style/behavior changes, consistent domain language. They're complementary and often used together.

**Q: What is hallucination in LLMs?**
> LLMs generate plausible-sounding but factually incorrect text. Causes: training data gaps, overconfident generation, no grounding in facts. Mitigations: RAG (ground in retrieved facts), temperature=0, chain-of-thought prompting, self-consistency checking.

**Q: What is the difference between BERT and GPT?**
> BERT is encoder-only with bidirectional attention — good for understanding tasks (classification, NER, QA). GPT is decoder-only with causal (left-to-right) attention — good for generation tasks (completion, chatting, writing).

**Q: What is cross-entropy loss?**
> Cross-entropy measures the difference between the predicted probability distribution and the true distribution. For classification with classes [cat, dog, bird], if true label is "cat" (1,0,0) and model predicts (0.7,0.2,0.1), cross-entropy = -log(0.7) ≈ 0.36. Perfect prediction = 0 loss.

**Q: What is embedding dimensionality and why does it matter?**
> Higher dimensions = more information capacity = better representations, but slower and more memory. Lower dimensions = faster but may lose nuance. Trade-off: 384-dim (fast, good) vs 1536-dim (slower, better) vs 3072-dim (best, most expensive).

**Q: What is a vector database good for vs a traditional database?**
> Traditional DB: exact matches, SQL queries, structured data. Vector DB: semantic similarity search, finding "meaning-similar" content, unstructured data. Traditional: "find user with id=5." Vector: "find documents about climate change."

---

### 8.2 Architecture Interview: Complete Sample Answer

**Q: "Design a customer support AI chatbot for an e-commerce company"**

**Your Answer Structure:**

```
1. REQUIREMENTS CLARIFICATION (2 min)
   - How many products? How many support tickets/day?
   - What languages? Any compliance requirements?
   - Real-time or batch? What's the latency SLA?

2. HIGH-LEVEL ARCHITECTURE
   - RAG-based system (not pure fine-tuning) because:
     → Product catalog changes frequently
     → Need to cite specific policies/orders
     → Can't bake thousands of products into weights

3. COMPONENTS:
   ├── Knowledge Base Indexing
   │   ├── Data sources: product catalog, FAQs, policies, order history
   │   ├── Processing: chunk PDFs, normalize product data
   │   ├── Embedding: text-embedding-3-small
   │   └── Storage: Pinecone (managed, scalable)
   │
   ├── Query Pipeline
   │   ├── Intent classification: "refund?", "track order?", "product info?"
   │   ├── Query expansion: rephrase for better retrieval
   │   ├── Hybrid search: semantic + keyword
   │   └── Re-ranking: cross-encoder for precision
   │
   ├── Generation
   │   ├── LLM: GPT-4o or Claude 3.5 Sonnet
   │   ├── Prompt: persona + retrieved context + history
   │   └── Guardrails: no competitor mentions, stay on-topic
   │
   └── Production Concerns
       ├── Caching: cache common queries (Redis)
       ├── Fallback: escalate to human if confidence < 70%
       ├── Monitoring: track query latency, user satisfaction
       └── Safety: PII detection, harmful content filtering

4. EVALUATION METRICS:
   - Faithfulness (RAGAS): is answer grounded in retrieved docs?
   - First Contact Resolution rate
   - Customer satisfaction (CSAT)
   - Escalation rate (lower = better)
   - Latency p95 < 3 seconds

5. ITERATION PLAN:
   Week 1: Basic RAG with FAQ data
   Week 2: Add product catalog, improve chunking
   Week 3: Add conversation memory, order lookup tool
   Week 4: A/B testing, collect user feedback, fine-tune
```

---

### 8.3 Key Terms — Final Glossary

| Term | One-Line Definition |
|------|---------------------|
| **Inference** | Using a trained model to make predictions |
| **Training** | Adjusting model weights using data + backprop |
| **Pre-training** | Training from scratch on massive general data |
| **Fine-tuning** | Adapting pre-trained model to specific task |
| **Zero-shot** | Model performs task without any task-specific examples |
| **Few-shot** | Model gets 2-5 examples in prompt, then answers |
| **Prompt engineering** | Crafting inputs to get better LLM outputs |
| **Chain-of-Thought** | "Let's think step by step" — improves reasoning |
| **In-context learning** | Model learns from examples in the prompt |
| **Quantization** | Reduce model size by using lower precision (FP32→INT4) |
| **VRAM** | GPU memory — limits model size you can load |
| **Perplexity** | How "surprised" a language model is by text — lower=better |
| **BLEU** | Metric for translation quality |
| **F1 Score** | Harmonic mean of precision & recall |
| **ROC-AUC** | Classification model quality (1.0 = perfect) |
| **Latency** | Time for one inference request |
| **Throughput** | Requests processed per second |
| **Token/second** | Speed of LLM generation |
| **MoE** | Mixture of Experts — only subset of model runs per token |
| **RLHF** | Training with human feedback to align model behavior |

---

## 📚 Recommended Learning Path for a Fresher

```
Month 1: Foundations
├── Numpy, Pandas, Matplotlib (1 week)
├── Sklearn + Classical ML (1 week)
├── PyTorch basics + MNIST (1 week)
└── Build: Digit classifier from scratch

Month 2: Deep Learning
├── CNNs for image classification
├── RNNs/LSTMs for sequences
├── Transformers + HuggingFace
└── Build: Sentiment analyzer with BERT

Month 3: LLMs & RAG
├── LangChain fundamentals
├── Vector databases (ChromaDB/FAISS)
├── RAG pipeline construction
└── Build: Document Q&A chatbot (like this project!)

Month 4: Production
├── LangGraph for multi-step agents
├── Evaluation (RAGAS)
├── Deployment (FastAPI + Docker)
└── Build: Complete agentic application

Continuous: 
├── Read: Papers with Code, Arxiv
├── Follow: HuggingFace blog, OpenAI blog
└── Practice: Kaggle competitions
```

---

*This concludes the AI Engineering Textbook. You now have the theoretical foundation to speak confidently in any AI engineering interview.*

**Files in this series:**
1. `AI_Engineering_Textbook_Part1.md` — Python Libraries & Neural Networks
2. `AI_Engineering_Textbook_Part2.md` — NLP, Tokenizers, Embeddings & Transformers  
3. `AI_Engineering_Textbook_Part3.md` — LLMs, RAG, LangChain & Key Models
4. `AI_Engineering_Textbook_Part4.md` — Architecture Design, Training & Interview Q&A (this file)
