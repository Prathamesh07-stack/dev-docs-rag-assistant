# 🧠 AI Engineering Textbook — Part 3: LLMs, RAG, LangChain & Graph Agents

---

## CHAPTER 4: Large Language Models (LLMs)

---

### 4.1 What is an LLM?

**🎤 Interview Answer:**
A Large Language Model (LLM) is a transformer-based neural network trained on massive text corpora (hundreds of billions to trillions of tokens) to predict the next token in a sequence. Through this self-supervised pre-training objective, LLMs develop emergent capabilities including reasoning, instruction following, code generation, and in-context learning. Notable LLMs include GPT-4, Claude, Gemini, and the open-source LLaMA family.

**👶 Simple Explanation:**
An LLM is a model trained on basically the entire internet. It learned by playing "complete this sentence" trillions of times. After doing that so many times, it accidentally learned: grammar, facts, reasoning, coding, math — almost everything humans write about. ChatGPT is an LLM you talk to through a chat interface.

**LLM Training Stages:**
```
Stage 1: Pre-training
"Predict next token" on massive corpus
→ Model learns language, facts, reasoning

Stage 2: Supervised Fine-Tuning (SFT)  
Trained on (instruction → good response) pairs
→ Model learns to follow instructions

Stage 3: RLHF (Reinforcement Learning from Human Feedback)
Humans rank responses → Train reward model → RL to maximize reward
→ Model becomes helpful, harmless, honest
```

**Major LLMs Comparison:**
| Model | Provider | Params | Context | Open? |
|-------|----------|--------|---------|-------|
| GPT-4o | OpenAI | Unknown | 128K | No |
| Claude 3.5 Sonnet | Anthropic | Unknown | 200K | No |
| Gemini 1.5 Pro | Google | Unknown | 1M | No |
| LLaMA 3.1 405B | Meta | 405B | 128K | Yes |
| Mistral Large | Mistral | Unknown | 128K | Partial |
| Qwen 2.5 72B | Alibaba | 72B | 128K | Yes |
| DeepSeek-V3 | DeepSeek | 671B (MoE) | 128K | Yes |

---

### 4.2 Tokens, Context Window & Temperature

**🎤 Interview Answer:**
The context window defines the maximum number of tokens an LLM can process in a single forward pass — encompassing both the input prompt and generated output. Temperature is a generation parameter controlling output randomness: at 0 the model is deterministic (greedy decoding), at 1 it samples from the full probability distribution, and above 1 introduces more randomness.

**👶 Simple Explanation:**
- **Context window**: The LLM's "working memory." GPT-4 can remember 128,000 tokens (~96,000 words) at once. Old models had 4,000 — like having amnesia after every paragraph.
- **Temperature**: Creativity dial. 0 = robot-precise. 1 = creative. 2 = random garbage.
- **Top-P (nucleus sampling)**: Instead of top-K most likely words, take however many words are needed to cover P% probability mass.

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user",   "content": "Explain quantum computing simply."}
    ],
    temperature=0.7,    # 0=deterministic, 1=creative
    max_tokens=500,     # Max output tokens
    top_p=0.9,          # Nucleus sampling
    frequency_penalty=0.1,  # Penalize repeating words
)

print(response.choices[0].message.content)
print(f"Tokens used: {response.usage.total_tokens}")
```

---

### 4.3 Fine-Tuning LLMs

**🎤 Interview Answer:**
Fine-tuning adapts a pre-trained LLM to specific domains or tasks using domain-specific labeled data. Full fine-tuning updates all parameters (expensive), while Parameter-Efficient Fine-Tuning (PEFT) methods like LoRA (Low-Rank Adaptation) freeze most parameters and only train small adapter matrices — reducing compute requirements by 10-100x while achieving comparable performance.

**👶 Simple Explanation:**
You take a smart general-purpose model (like a graduated doctor) and teach them specialist skills (like becoming a cardiologist). The base knowledge stays, you just add domain-specific skills on top. LoRA is a clever trick where instead of rewriting the whole textbook, you add sticky notes — tiny additions that teach the new skill.

**Fine-Tuning Methods:**
| Method | Cost | Performance | Description |
|--------|------|-------------|-------------|
| Full Fine-Tuning | Very High | Highest | Update all parameters |
| LoRA | Low | Near-full | Train low-rank adapter matrices |
| QLoRA | Very Low | Near-LoRA | Quantized base + LoRA |
| Prompt Tuning | Minimal | Good | Train soft prompts only |
| RLHF | High | Alignment | Human feedback + RL |
| DPO | Medium | Alignment | Direct preference optimization |

```python
# QLoRA Fine-tuning with HuggingFace (conceptual)
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType

# Load model in 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype="float16"
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct",
    quantization_config=bnb_config,
    device_map="auto"
)

# Apply LoRA
lora_config = LoraConfig(
    r=8,                          # Rank of adapter matrices
    lora_alpha=32,                # Scaling factor
    target_modules=["q_proj", "v_proj"],  # Which layers to adapt
    lora_dropout=0.05,
    task_type=TaskType.CAUSAL_LM
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# trainable params: 4,194,304 || all params: 8,033,669,120 || trainable%: 0.05%
```

---

## CHAPTER 5: RAG — Retrieval-Augmented Generation

---

### 5.1 What is RAG?

**🎤 Interview Answer:**
Retrieval-Augmented Generation (RAG) is an architectural pattern that enhances LLM responses by dynamically retrieving relevant information from an external knowledge base and injecting it into the prompt context. It addresses key LLM limitations: knowledge cutoff dates, hallucinations on domain-specific knowledge, and context window constraints. RAG separates "memory" from "reasoning" — the vector database stores facts, the LLM reasons over them.

**👶 Simple Explanation:**
An LLM's training data has a cutoff date and it doesn't know YOUR company's internal documents. RAG fixes this. Instead of asking the LLM to "remember" everything, we:
1. Search our own document database for relevant info
2. Stuff that info into the prompt
3. Let the LLM answer using THAT retrieved info

It's like an open-book exam instead of closed-book. The LLM is smarter when it can "look things up."

**RAG Pipeline:**
```
User Question
      ↓
[Embed the Question]  →  768-dim vector
      ↓
[Search Vector DB]    →  Top-K most similar chunks
      ↓
[Build Prompt]        →  "Using this context: {chunks} Answer: {question}"
      ↓
[LLM Generates Answer]
      ↓
Response to User
```

---

### 5.2 Chunking Strategies

**🎤 Interview Answer:**
Chunking is the process of splitting source documents into smaller, semantically coherent segments before embedding and indexing. Chunk size is a critical hyperparameter: chunks too large dilute relevant information and exceed context windows; chunks too small lose needed context. Optimal chunking depends on document structure, embedding model constraints, and retrieval precision requirements.

**👶 Simple Explanation:**
You can't feed an entire 500-page PDF to the vector database at once. You slice it into small pieces (chunks) — like cutting a loaf of bread. Each chunk gets its own embedding. When a user asks a question, you find the most relevant chunks (not entire document) to answer it.

**Chunking Types:**

#### 1. Fixed-Size Chunking
```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50  # Overlap prevents cutting mid-thought
)

text = "Long document text here..."
chunks = splitter.split_text(text)
```

#### 2. Recursive Character Text Splitter (Most Common)
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]  # Try each separator in order
)
chunks = splitter.split_documents(documents)
```

#### 3. Semantic Chunking (Best Quality)
```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

chunker = SemanticChunker(
    OpenAIEmbeddings(),
    breakpoint_threshold_type="percentile",  # Split where meaning changes
    breakpoint_threshold_amount=95
)
```

**Chunking Strategy Comparison:**
| Strategy | Description | Best For |
|----------|-------------|---------|
| Fixed-size | Split every N characters | Simple, quick |
| Recursive | Split by paragraphs → sentences → words | General docs |
| Semantic | Split where meaning changes | High accuracy |
| Markdown/HTML | Split by headers/tags | Structured docs |
| Sentence | Split by sentences | QA tasks |
| Token-based | Split by token count | LLM-aware chunking |

---

### 5.3 Types of RAG

**🎤 Interview Answer:**
RAG has evolved from naive single-pass retrieval to sophisticated multi-step architectures. Key variants include: Naive RAG (basic retrieve-then-generate), Advanced RAG (query rewriting, re-ranking, hybrid search), Modular RAG (pluggable components), Corrective RAG (self-correction loop), and Agentic RAG (LLM decides when/how to retrieve).

**RAG Evolution:**
```
Naive RAG → Advanced RAG → Modular RAG → Agentic RAG
  (2023)       (2023)         (2024)        (2024-25)
```

**RAG Types Explained:**

| Type | How It Works | Advantage |
|------|-------------|-----------|
| **Naive RAG** | Chunk → Embed → Store → Retrieve → Generate | Simple, works for many cases |
| **Advanced RAG** | + Query rewriting + re-ranking | Higher accuracy |
| **Hybrid RAG** | Vector search + BM25 keyword search combined | Best recall |
| **Corrective RAG** | LLM checks if retrieved docs are relevant | Reduces hallucinations |
| **Self-RAG** | LLM decides when to retrieve | Efficient |
| **GraphRAG** | Knowledge graphs + vector search | Structured knowledge |
| **Agentic RAG** | Agent calls tools including retrieval | Most flexible |

```python
# Naive RAG with LangChain
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. Load documents
loader = PyPDFLoader("my_document.pdf")
docs = loader.load()

# 2. Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# 3. Embed and store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# 4. Create retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 5. Create RAG chain
llm = ChatOpenAI(model="gpt-4o", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# 6. Ask questions
result = qa_chain.invoke({"query": "What is the main topic?"})
print(result['result'])
```

---

### 5.4 LangChain — Deep Dive

**🎤 Interview Answer:**
LangChain is a framework for building LLM-powered applications through composable abstractions. Its core primitives are: Chains (sequential LLM workflows), Agents (LLMs that reason about tool use), Memory (conversation history management), Retrievers (document fetching), and Tools (external API integrations). LangChain Expression Language (LCEL) provides a pipe-based syntax for composing chains.

**Key LangChain Components:**

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 1. LCEL Chain (pipe syntax)
llm = ChatOpenAI(model="gpt-4o")
prompt = ChatPromptTemplate.from_template(
    "Answer the question based on:\n{context}\n\nQuestion: {question}"
)
chain = prompt | llm | StrOutputParser()

# 2. Memory for conversation
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain

memory = ConversationBufferWindowMemory(k=5)  # Remember last 5 exchanges
conversation = ConversationChain(llm=llm, memory=memory)

response1 = conversation.predict(input="My name is Prathamesh")
response2 = conversation.predict(input="What's my name?")  # Remembers!
print(response2)  # "Your name is Prathamesh"

# 3. Tools & Agents
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.tools import DuckDuckGoSearchRun

search_tool = DuckDuckGoSearchRun()
tools = [search_tool]

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
result = executor.invoke({"input": "What's the latest news about AI?"})
```

**LangChain Memory Types:**
| Memory | Description |
|--------|-------------|
| `ConversationBufferMemory` | All messages kept |
| `ConversationBufferWindowMemory` | Last K messages |
| `ConversationSummaryMemory` | Summarizes old messages |
| `VectorStoreRetrieverMemory` | Retrieves relevant memories |
| `EntityMemory` | Tracks named entities |

---

### 5.5 LangGraph — Stateful AI Agents

**🎤 Interview Answer:**
LangGraph is a framework built on LangChain for creating stateful, multi-actor AI workflows modeled as directed graphs. Each node is a function that processes state, edges define control flow (including conditional routing), and state is a typed dictionary shared across all nodes. This enables complex agentic behaviors: loops, branching, human-in-the-loop checkpoints, and multi-agent coordination.

**👶 Simple Explanation:**
Imagine a workflow where an AI needs to: (1) understand the question, (2) search databases, (3) check if the answer is good, (4) if not good: go back and search again, (5) if good: respond. This is a loop — LangChain alone can't do this. LangGraph lets you build these flowchart-like Agent workflows where the AI can loop back, branch, and make decisions.

```
                    ┌─────────────────────────────────┐
                    │           LangGraph State        │
                    └─────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
      [understand]           [search_docs]            [generate]
           │                        │                        │
           └────────────────────────┘                        │
                         │                                   │
                    [check_quality] ──── GOOD ──────────────►│
                         │                                   │
                       BAD (loop)                            │
                         │                                   ▼
                         └──────────────────────────► [final response]
```

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

# Define state
class AgentState(TypedDict):
    question: str
    documents: List[str]
    answer: str
    quality_check: str

llm = ChatOpenAI(model="gpt-4o")

# Define nodes (each is a function)
def retrieve_documents(state: AgentState) -> AgentState:
    # Simulate retrieval
    state["documents"] = [f"Relevant doc for: {state['question']}"]
    return state

def generate_answer(state: AgentState) -> AgentState:
    context = "\n".join(state["documents"])
    response = llm.invoke(f"Context: {context}\nQuestion: {state['question']}")
    state["answer"] = response.content
    return state

def check_quality(state: AgentState) -> AgentState:
    # Check if answer is satisfactory
    check = llm.invoke(f"Is this answer good? '{state['answer']}' Reply: GOOD or BAD")
    state["quality_check"] = check.content
    return state

def route_after_check(state: AgentState) -> str:
    if "GOOD" in state["quality_check"]:
        return "end"
    return "retrieve"  # Loop back

# Build graph
graph = StateGraph(AgentState)
graph.add_node("retrieve", retrieve_documents)
graph.add_node("generate", generate_answer)
graph.add_node("check", check_quality)

graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", "check")
graph.add_conditional_edges("check", route_after_check, 
                             {"end": END, "retrieve": "retrieve"})

app = graph.compile()
result = app.invoke({"question": "What is RAG?", "documents": [], "answer": "", "quality_check": ""})
print(result["answer"])
```

---

## CHAPTER 6: Important Models & Benchmarks

---

### 6.1 BERT

**🎤 Interview Answer:**
BERT (Bidirectional Encoder Representations from Transformers) is a pre-trained encoder-only transformer from Google (2018). It uses Masked Language Modeling (MLM) and Next Sentence Prediction (NSP) as self-supervised pre-training objectives. BERT's bidirectional attention means each token attends to surrounding tokens on both sides, enabling deep contextual understanding. It revolutionized NLP benchmarks and is commonly used for embeddings, classification, NER, and QA.

**👶 Simple Explanation:**
BERT reads sentences in BOTH directions at once (left-to-right AND right-to-left), making it understand context much better. Trained on "fill in the blank" — "The [MASK] sat on the mat" → "cat." After training this billions of times, it deeply understands language. Great for understanding tasks.

```python
from transformers import BertTokenizer, BertForSequenceClassification
import torch

# BERT for sentiment classification
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

text = "This movie is absolutely amazing!"
inputs = tokenizer(text, return_tensors='pt', 
                   padding=True, truncation=True, max_length=512)

with torch.no_grad():
    outputs = model(**inputs)
    logits = outputs.logits
    prediction = torch.argmax(logits, dim=-1)
    print("Positive" if prediction == 1 else "Negative")
```

**BERT Variants:**
| Model | Size | Notes |
|-------|------|-------|
| BERT-base | 110M | 12 layers, 768 hidden |
| BERT-large | 340M | 24 layers, 1024 hidden |
| RoBERTa | 125M | Improved BERT training |
| DistilBERT | 66M | 40% smaller, 97% performance |
| ALBERT | 12M | Parameter sharing, tiny |
| DeBERTa | 184M | Best BERT variant for NLU |

---

### 6.2 GPT Family

**🎤 Interview Answer:**
GPT (Generative Pre-trained Transformer) models are decoder-only transformers trained with causal language modeling — predicting the next token given all previous tokens. This autoregressive training makes them naturally suited for text generation. GPT-4 introduced multimodal capabilities (vision+text), while GPT-4o further improved latency for production use.

**👶 Simple Explanation:**
While BERT reads bidirectionally to understand, GPT generates text left-to-right, one word at a time, like autocomplete on steroids. It predicts: "given all words so far, what word comes next?" Do this thousands of times = you get paragraphs, essays, code.

**GPT Evolution:**
```
GPT-1 (2018) → GPT-2 (2019) → GPT-3 (2020) → ChatGPT (2022)
→ GPT-4 (2023) → GPT-4o (2024) → o1 / o3 (2024-25)
```

---

### 6.3 MNIST — The "Hello World" of AI

**🎤 Interview Answer:**
MNIST (Modified National Institute of Standards and Technology) is a dataset of 70,000 handwritten digit images (28×28 grayscale) used as a benchmark for image classification. It is the standard "hello world" for computer vision — every ML practitioner starts here. Modern models achieve >99.7% accuracy on it.

**👶 Simple Explanation:**
MNIST is 70,000 handwritten numbers 0-9 drawn by humans. You train a model to look at a handwritten "7" and predict "7". It's the simplest possible image classification task — used to test if your model setup is correct before moving to harder problems.

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

# Load MNIST data
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

train_data = datasets.MNIST('./data', train=True, download=True, transform=transform)
test_data  = datasets.MNIST('./data', train=False, transform=transform)

train_loader = DataLoader(train_data, batch_size=64, shuffle=True)
test_loader  = DataLoader(test_data,  batch_size=64)

# Simple CNN for MNIST
class MNISTNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 32, 3),  # 28×28 → 26×26
            nn.ReLU(),
            nn.MaxPool2d(2),      # 26×26 → 13×13
            nn.Conv2d(32, 64, 3), # 13×13 → 11×11
            nn.ReLU(),
            nn.MaxPool2d(2),      # 11×11 → 5×5
            nn.Flatten(),
            nn.Linear(64*5*5, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 10)   # 10 digit classes
        )
    def forward(self, x): return self.net(x)

model = MNISTNet()
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# Train one epoch
model.train()
for batch_idx, (data, target) in enumerate(train_loader):
    optimizer.zero_grad()
    output = model(data)
    loss = criterion(output, target)
    loss.backward()
    optimizer.step()
    if batch_idx % 100 == 0:
        print(f'Loss: {loss.item():.4f}')
```

---

*End of Part 3. Continue to Part 4: Architecture Design, Model Training & Interview Q&A*
