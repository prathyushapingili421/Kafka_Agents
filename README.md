# Kafka Multi-Agent System with GEval Evaluation

A production-ready multi-agent system using Apache Kafka for message coordination and GEval (DeepEval) for automated quality assessment.

## 🎯 Project Overview

This system demonstrates how to build, coordinate, and evaluate multiple AI agents working together through Kafka message queues. Each agent specializes in a specific task, and automated evaluation measures the quality of their collaboration.

### System Architecture

```
┌─────────────┐
│    User     │
│  Question   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                    Kafka Topics                          │
├─────────────┬─────────────┬─────────────┬──────────────┤
│    inbox    │    tasks    │   drafts    │    final     │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬───────┘
       │             │             │             │
       ▼             ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│ Planner  │─▶│  Writer  │─▶│ Reviewer │─▶│  Evaluator   │
│  Agent   │  │  Agent   │  │  Agent   │  │    (GEval)   │
└──────────┘  └──────────┘  └──────────┘  └──────┬───────┘
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │ evaluation.json │
                                         └─────────────────┘
```

### Agents

1. **Planner Agent**: Analyzes questions and creates structured plans
2. **Writer Agent**: Uses LangChain + OpenAI to draft comprehensive answers
3. **Reviewer Agent**: Performs quality checks and approves final answers
4. **Evaluator Agent**: Uses GEval to score each stage with LLM-as-a-judge

### Evaluation Metrics

- **Plan Quality** (0-1): Structure, clarity, actionability of the plan
- **Draft Helpfulness** (0-1): Accuracy, completeness of the answer
- **Final Answer Quality** (0-1): Overall quality of the final output
- **Draft-to-Final Improvement** (0-1): Value added by the reviewer

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- OpenAI API key (for Writer agent)
- Ollama (recommended) OR OpenAI API key (for Evaluator)

### 1. Clone and Setup

```bash
# Clone repository
git clone <your-repo-url>
cd kafka-multi-agent-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Minimum configuration**:
```bash
OPENAI_API_KEY=sk-your-key-here  # Required for Writer
USE_OLLAMA=true                   # Use Ollama for evaluation (free)
OLLAMA_MODEL=llama3.2             # Or any Ollama model
```

### 3. Start Infrastructure

**Start Kafka**:
```bash
docker-compose up -d

# Verify
docker ps | grep kafka
```

**Start Ollama** (if using for evaluation):
```bash
# Install from https://ollama.ai
ollama serve

# In another terminal, pull model
ollama pull llama3.2

# Verify
curl http://localhost:11434/api/tags
```

### 4. Start Agents (4 terminals)

**Terminal 1 - Planner**:
```bash
python planner.py
```

**Terminal 2 - Writer**:
```bash
python writer.py
```

**Terminal 3 - Reviewer**:
```bash
python reviewer.py
```

**Terminal 4 - Evaluator**:
```bash
python evaluator_enhanced.py
```

### 5. Run Test

**Terminal 5 - Test Script**:
```bash
python test_evaluation_enhanced.py
```

## 📊 Expected Results

### Sample Output

```
================================================================================
✅ GEVAL EVALUATION COMPLETED!
================================================================================

❓ Question: What are the benefits of using Kafka for microservices?
🤖 Model Used: ollama-llama3.2

📊 EVALUATION SCORES:
────────────────────────────────────────────────────────────────────────────────

1️⃣  PLAN QUALITY: 0.850/1.0 ✓ PASS
    📝 The plan demonstrates excellent structure with clear, actionable steps...

2️⃣  DRAFT HELPFULNESS: 0.822/1.0 ✓ PASS
    📝 The draft answer comprehensively addresses the question with accurate...

3️⃣  FINAL ANSWER QUALITY: 0.833/1.0 ✓ PASS
    📝 The final answer maintains high quality with professional presentation...

4️⃣  DRAFT-TO-FINAL IMPROVEMENT: 0.755/1.0 ✓ PASS
    📝 The reviewer maintained quality while making subtle improvements...

================================================================================
📈 OVERALL STATISTICS
================================================================================
  Average Score:     0.815/1.0
  Minimum Score:     0.755/1.0
  Maximum Score:     0.850/1.0
  All Tests Passed:  ✅ YES
  Quality Rating:    🌟 EXCELLENT
```

### Score Interpretation

| Score | Quality | Meaning |
|-------|---------|---------|
| 0.90-1.00 | 🌟 Excellent | Publication-ready |
| 0.80-0.89 | 👍 Good | High quality, minor improvements |
| 0.70-0.79 | ✓ Acceptable | Decent, some work needed |
| 0.60-0.69 | ⚠️ Fair | Meets minimum standards |
| 0.50-0.59 | ❌ Poor | Below standards |

## 📁 Project Structure

```
kafka-multi-agent-system/
├── agents/
│   ├── planner.py              # Plans question answering approach
│   ├── writer.py               # Writes draft answers using LangChain
│   ├── reviewer.py             # Reviews and approves drafts
│   └── evaluator.py   # GEval evaluation with Ollama
├── tests/
│   └── test_evaluation.py  # End-to-end test script
├── utils/
│   ├── send_question.py        # Simple question sender
│   └── read_final.py           # Read final answers
├── docker-compose.yml          # Kafka infrastructure
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🔧 Configuration Options

### Using OpenAI for Evaluation (Instead of Ollama)

```bash
# In .env
USE_OLLAMA=false
OPENAI_API_KEY=sk-your-key-here
```

### Trying Different Ollama Models

```bash
# Fastest (recommended for testing)
OLLAMA_MODEL=llama3.2    # 3B parameters

# More capable (slower)
OLLAMA_MODEL=mistral     # 7B parameters
OLLAMA_MODEL=llama2      # 13B parameters

# Download model
ollama pull mistral
```

### Adjusting Writer Model

```bash
# In .env
OPENAI_MODEL=gpt-4o-mini     # Default, fast & cheap
OPENAI_MODEL=gpt-4o          # More capable
OPENAI_TEMPERATURE=0.7       # Creativity (0.0-1.0)
```

## 🐛 Troubleshooting

### Kafka Issues

**Problem**: `NoBrokersAvailable` error
```bash
# Check if Kafka is running
docker ps | grep kafka

# Restart Kafka
docker-compose restart

# Check logs
docker-compose logs kafka
```

**Problem**: Topics not found
```bash
# Create topics manually
docker exec -it kafka kafka-topics --create --topic inbox --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker exec -it kafka kafka-topics --create --topic tasks --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker exec -it kafka kafka-topics --create --topic drafts --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker exec -it kafka kafka-topics --create --topic final --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

### Ollama Issues

**Problem**: Connection refused
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

**Problem**: Model not found
```bash
# List available models
ollama list

# Pull required model
ollama pull llama3.2
```

### Agent Issues

**Problem**: Import errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check installation
pip list | grep -E "kafka|langchain|deepeval"
```

**Problem**: OpenAI API errors
```bash
# Verify API key
echo $OPENAI_API_KEY

# Check .env file
cat .env | grep OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```



This project demonstrates:

1. **Multi-Agent Coordination**: Using Kafka for async agent communication
2. **LLM Integration**: Practical use of LangChain and OpenAI
3. **Automated Evaluation**: LLM-as-a-judge with GEval metrics
4. **Production Patterns**: Error handling, logging, monitoring
5. **Scalability**: Message queues for distributed systems

## 🔬 Experimentation Ideas

1. **Add More Agents**: Research, fact-checker, summarizer
2. **Custom Metrics**: Domain-specific evaluation criteria
3. **Different LLMs**: Compare OpenAI vs Ollama vs Claude
4. **Batch Processing**: Handle multiple questions concurrently
5. **Feedback Loops**: Use evaluation results to improve agents

## 📊 Monitoring

### View Live Messages

```bash
# Monitor inbox
docker exec -it kafka kafka-console-consumer --topic inbox --bootstrap-server localhost:9092 --from-beginning

# Monitor final answers
docker exec -it kafka kafka-console-consumer --topic final --bootstrap-server localhost:9092 --from-beginning
```

### Check Agent Logs

Each agent prints status to console. Monitor for:
- ✅ Success messages
- ⏳ Processing indicators
- ❌ Error messages

### View Evaluation Results

```bash
# List all results
ls -lh evaluation_results_*.json

# Pretty print latest result
cat evaluation_results_*.json | jq .

# View summary
jq '.overall' evaluation_results_*.json
```


## 📝 License

MIT License - feel free to use for learning and projects.

## 🙏 Acknowledgments

- **DeepEval**: Evaluation framework
- **LangChain**: LLM orchestration
- **Apache Kafka**: Message streaming
- **Ollama**: Local LLM inference
- **OpenAI**: Language models


