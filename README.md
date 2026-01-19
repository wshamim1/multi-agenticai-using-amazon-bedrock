# 🤖 Multi-Agent AI System with Amazon Bedrock

A production-ready, enterprise-grade multi-agent AI system built on Amazon Bedrock, featuring intelligent agent orchestration, RAG-powered knowledge base, and an intuitive Streamlit interface. Powered by **Amazon Nova Pro 1.0** for cutting-edge multimodal AI capabilities.

[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange)](https://aws.amazon.com/bedrock/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Knowledge Base](#-knowledge-base)
- [Usage Examples](#-usage-examples)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Maintenance](#-maintenance)
- [Troubleshooting](#-troubleshooting)
- [Security](#-security)
- [Cost Optimization](#-cost-optimization)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

This system demonstrates a sophisticated multi-agent architecture where a **Supervisor Agent** intelligently routes user queries to specialized **Collaborator Agents**, each optimized for specific domains. The system leverages Amazon Bedrock's latest foundation models and integrates seamlessly with AWS services for a complete AI solution.

### What Makes This Special?

- **🧠 Intelligent Routing**: Supervisor agent automatically determines which specialist to consult
- **🔄 Multi-Agent Collaboration**: Agents work together to provide comprehensive answers
- **📚 RAG Integration**: Knowledge base provides context-aware responses using your documents
- **🎯 Specialized Expertise**: Each agent is fine-tuned for its specific domain
- **🚀 Production Ready**: Comprehensive error handling, logging, and monitoring
- **♻️ Idempotent Deployment**: Safe to run multiple times without conflicts

---

## ✨ Key Features

### 🤖 Multi-Agent System

- **Supervisor Agent**: Orchestrates query routing and agent collaboration
- **Weather Agent** 🌤️: Real-time weather information and forecasts
- **Stock Market Agent** 📈: Stock prices, market data, and financial analysis
- **News Agent** 📰: Latest news, headlines, and current events

### 🧠 AI Capabilities

- **Amazon Nova Pro 1.0**: Latest AWS foundation model with multimodal support (text, images, video)
- **RAG (Retrieval Augmented Generation)**: Context-aware responses using your knowledge base
- **Intelligent Query Understanding**: Natural language processing for intent detection
- **Multi-Turn Conversations**: Maintains context across interactions

### 🏗️ Infrastructure

- **AWS Lambda**: Serverless function execution for agent actions
- **Amazon S3**: Document storage for knowledge base
- **OpenSearch Serverless**: Vector database for semantic search
- **IAM**: Fine-grained security and access control

### 💻 User Interface

- **Streamlit Web App**: Modern, responsive chat interface
- **Multiple Modes**: Agent chat, knowledge base search, text generation, document analysis
- **Real-time Responses**: Streaming responses for better UX
- **Session Management**: Persistent conversation history

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streamlit Web Interface                     │
│                    (Interactive Chat UI)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ User Query
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Supervisor Agent                             │
│              (Amazon Nova Pro 1.0 + RAG)                         │
│                                                                   │
│  • Analyzes user intent                                          │
│  • Routes to appropriate collaborator                            │
│  • Queries knowledge base when needed                            │
│  • Synthesizes final response                                    │
└──────┬──────────────┬──────────────┬──────────────┬─────────────┘
       │              │              │              │
       │ (Delegates)  │              │              │
       ▼              ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Weather  │   │  Stock   │   │   News   │   │Knowledge │
│  Agent   │   │  Agent   │   │  Agent   │   │   Base   │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │
     │ (Invokes)    │              │              │
     ▼              ▼              ▼              │
┌─────────────────────────────────────────┐      │
│      AWS Lambda Functions               │      │
│  • Weather data retrieval               │      │
│  • Stock market API calls               │      │
│  • News aggregation                     │      │
└─────────────────────────────────────────┘      │
                                                  │
                                                  │ (RAG Query)
                                                  ▼
                                    ┌─────────────────────────┐
                                    │   Knowledge Base        │
                                    │   (RAG System)          │
                                    └──────┬──────────┬───────┘
                                           │          │
                                    ┌──────▼──┐  ┌───▼────────┐
                                    │ S3      │  │ OpenSearch │
                                    │ Bucket  │  │ Serverless │
                                    │(Docs)   │  │ (Vectors)  │
                                    └─────────┘  └────────────┘
```

### Component Interaction Flow

1. **User Input** → Streamlit UI captures user query
2. **Supervisor Analysis** → Determines intent and required agent(s)
3. **Agent Delegation** → Routes to Weather/Stock/News agent or Knowledge Base
4. **Action Execution** → Lambda functions perform specialized tasks
5. **Response Synthesis** → Supervisor combines results into coherent answer
6. **UI Display** → Formatted response shown to user

---

## 📋 Prerequisites

### Required

- **Python 3.11+** - Latest Python version recommended
- **AWS Account** - With Bedrock access enabled
- **AWS CLI** - Configured with appropriate credentials
- **IAM Permissions** - Admin or equivalent for resource creation

### AWS Bedrock Model Access

Enable the following models in AWS Bedrock Console:

1. **Amazon Nova Pro 1.0** (`amazon.nova-pro-v1:0`) - Primary agent model
2. **Amazon Titan Embed Text v1** - For embeddings
3. **Amazon Titan Text Premier v1** (optional) - For knowledge base

### System Requirements

- **Memory**: 4GB RAM minimum
- **Storage**: 1GB free space
- **Network**: Internet connection for AWS API calls

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd multi-agenticai-using-amazon-bedrock
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure AWS Credentials

```bash
aws configure
```

Enter your credentials:
- **AWS Access Key ID**: Your access key
- **AWS Secret Access Key**: Your secret key
- **Default region**: `us-east-1` (recommended)
- **Output format**: `json`

### 4. Deploy the System

```bash
python main.py deploy
```

This comprehensive deployment will:

✅ Create IAM roles and policies with least privilege  
✅ Set up S3 bucket with encryption  
✅ Deploy Lambda functions for agent actions  
✅ Create OpenSearch Serverless collection  
✅ Initialize Knowledge Base with vector store  
✅ Upload sample documents from `data/` directory  
✅ Sync Knowledge Base to ingest and index documents  
✅ Deploy Supervisor Agent with Nova Pro 1.0  
✅ Deploy Collaborator Agents (Weather, Stock, News)  
✅ Associate Knowledge Base with Supervisor  
✅ Link Collaborators to Supervisor  

**Deployment Time**: ~10-15 minutes (OpenSearch collection creation is the longest step)

### 5. Launch the Web Interface

```bash
streamlit run streamlit_app.py
```

Open your browser to: **http://localhost:8501**

### 6. Start Chatting!

Try these example queries:
- "What's the weather in New York City?"
- "Get me the stock price for AAPL"
- "Show me today's top tech news"
- "How does the multi-agent system work?"

---

## 📁 Project Structure

```
multi-agenticai-using-amazon-bedrock/
│
├── core/                           # Core system modules
│   ├── agent_manager.py           # Agent lifecycle management
│   ├── iam_manager.py             # IAM roles and policies
│   ├── storage_manager.py         # S3 operations
│   ├── lambda_manager.py          # Lambda deployment
│   ├── opensearch_manager.py      # OpenSearch setup
│   ├── knowledge_base_manager.py  # Knowledge Base operations
│   └── model_config_loader.py     # Model configuration loader
│
├── data/                           # Knowledge Base documents
│   ├── sample_kb_data.txt         # System documentation
│   ├── agent_capabilities.txt     # Agent features
│   ├── aws_bedrock_guide.txt      # Bedrock guide
│   ├── faq.txt                    # FAQs
│   └── README.md                  # Data guidelines
│
├── config.py                       # Central configuration
├── agents_config.py               # Agent definitions
├── orchestrator.py                # System orchestration
├── main.py                        # CLI entry point
├── streamlit_app.py               # Web UI application
├── cleanup.py                     # Resource cleanup
├── models_config.yaml             # Model configurations
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── ARTICLE.md                     # Technical article

```

### Key Files Explained

- **`main.py`**: Command-line interface for deployment and management
- **`streamlit_app.py`**: Interactive web application
- **`orchestrator.py`**: Coordinates the entire deployment process
- **`config.py`**: Centralized configuration management
- **`agents_config.py`**: Agent definitions and Lambda code
- **`cleanup.py`**: Safe resource deletion

---

## 📚 Knowledge Base

The system includes a comprehensive knowledge base that enables RAG (Retrieval Augmented Generation) for context-aware responses.

### Included Documents

| Document | Lines | Content |
|----------|-------|---------|
| **sample_kb_data.txt** | 145 | System architecture, agent capabilities, AWS services, best practices |
| **agent_capabilities.txt** | 200 | Detailed agent features, query patterns, integration examples |
| **aws_bedrock_guide.txt** | 350 | Comprehensive Bedrock documentation, models, security |
| **faq.txt** | 250 | Common questions, troubleshooting, cost optimization |

### Example Knowledge Base Queries

```
"How does the multi-agent system work?"
"What agents are available and what can they do?"
"How do I troubleshoot deployment errors?"
"What are the best practices for knowledge bases?"
"How much does this system cost to run?"
"Explain the RAG architecture"
```

### Adding Your Own Documents

1. **Place documents** in the `data/` directory
   - Supported formats: TXT, PDF, DOCX, HTML, MD
   - Max file size: 50MB per file

2. **Run deployment** to upload and index:
   ```bash
   python main.py deploy --upload-data
   ```

3. **Documents are automatically**:
   - Uploaded to S3
   - Chunked for optimal retrieval
   - Embedded using Titan
   - Indexed in OpenSearch

See `data/README.md` for detailed documentation guidelines.

---

## 🎯 Usage Examples

### Weather Queries

```
User: "What's the weather like in San Francisco?"
System: Routes to Weather Agent → Returns current conditions

User: "Will it rain in Seattle this week?"
System: Routes to Weather Agent → Returns 7-day forecast
```

### Stock Market Queries

```
User: "What's the current price of AAPL?"
System: Routes to Stock Agent → Returns real-time stock data

User: "Show me the market summary"
System: Routes to Stock Agent → Returns market overview
```

### News Queries

```
User: "What's the latest tech news?"
System: Routes to News Agent → Returns recent headlines

User: "Tell me about AI developments today"
System: Routes to News Agent → Returns AI-related news
```

### Knowledge Base Queries

```
User: "How does the supervisor agent work?"
System: Searches Knowledge Base → Returns documentation

User: "What are the deployment steps?"
System: Searches Knowledge Base → Returns setup guide
```

### Multi-Agent Queries

```
User: "What's the weather in NYC and how's the stock market?"
System: Routes to both Weather and Stock agents → Combines responses
```

---

## 🔧 Configuration

### Change Foundation Model

Edit `config.py`:

```python
@dataclass
class AgentConfig:
    foundation_model: str = "amazon.nova-pro-v1:0"  # Change this
```

Available models:
- `amazon.nova-pro-v1:0` (recommended)
- `anthropic.claude-3-sonnet-20240229-v1:0`
- `amazon.titan-text-premier-v1:0`

### Customize Agent Instructions

Edit `agents_config.py`:

```python
WEATHER_AGENT = {
    "name": "weather-agent",
    "instruction": "Your custom instruction here",
    "description": "Your custom description"
}
```

### Add New Collaborator Agent

1. **Define agent** in `agents_config.py`:
   ```python
   NEW_AGENT = {
       "name": "new-agent",
       "instruction": "Agent instructions",
       "lambda_code": "Lambda function code",
       "function_schema": {...}
   }
   ```

2. **Deploy**:
   ```bash
   python main.py deploy
   ```

### Environment Variables

```bash
export AWS_REGION=us-east-1
export AWS_PROFILE=your-profile
```

---

## 🚀 Deployment

### Full Deployment

```bash
python main.py deploy
```

### Selective Deployment

Disable specific agents:

```bash
python main.py deploy --disable-weather
python main.py deploy --disable-stock
python main.py deploy --disable-news
```

### Skip Data Upload

```bash
python main.py deploy --no-upload-data
```

### Custom Data Directory

```bash
python main.py deploy --data-dir /path/to/documents
```

### Idempotent Deployment

The system supports **safe re-deployment**:

```bash
python main.py deploy  # Run multiple times safely
```

The system will:
- ✅ Skip existing resources
- ✅ Update configurations if changed
- ✅ Handle conflicts gracefully
- ✅ Continue without errors

This is useful for:
- Updating agent configurations
- Adding new documents to knowledge base
- Recovering from partial deployments
- Testing deployment process

---

## 🛠️ Maintenance

### View Configuration

```bash
python main.py config
```

### Test Agent

```bash
python main.py test "What's the weather in Boston?"
```

### Update System

```bash
python main.py deploy  # Idempotent - safe to re-run
```

### Clean Up Resources

**⚠️ Warning**: This deletes ALL resources!

```bash
python cleanup.py
```

Removes:
- All agents and aliases
- Lambda functions
- S3 buckets and contents
- OpenSearch collections
- Knowledge bases
- IAM roles and policies

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Model Access Error

**Error**: `AccessDeniedException: Model access denied`

**Solution**: Enable model access in AWS Bedrock Console
1. Go to AWS Bedrock Console
2. Navigate to "Model access"
3. Request access for required models
4. Wait for approval (usually instant)

#### 2. IAM Permissions

**Error**: `AccessDeniedException: User is not authorized`

**Solution**: Ensure your IAM user has required permissions
```bash
# Required permissions:
- bedrock:*
- iam:*
- s3:*
- lambda:*
- aoss:*
```

#### 3. OpenSearch Timeout

**Error**: `Collection creation timeout`

**Solution**: OpenSearch collection creation takes 5-10 minutes. Wait and retry.

#### 4. Agent Not Found

**Error**: `Agent not found`

**Solution**: Ensure deployment completed successfully
```bash
python main.py deploy
```

#### 5. Lambda Invocation Error

**Error**: `Lambda function failed`

**Solution**: Check Lambda logs in CloudWatch
```bash
aws logs tail /aws/lambda/your-function-name --follow
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Get Help

1. Check logs in console output
2. Review CloudWatch logs for Lambda functions
3. Verify IAM permissions
4. Check AWS service quotas
5. Contact AWS Support for platform issues

---

## 🔐 Security

### IAM Best Practices

- ✅ Least privilege principle for all roles
- ✅ Separate roles for agents and Lambda functions
- ✅ No hardcoded credentials
- ✅ Regular permission audits

### Data Security

- ✅ S3 bucket encryption enabled (AES-256)
- ✅ OpenSearch uses AWS IAM authentication
- ✅ Lambda functions in VPC (optional)
- ✅ Secrets stored in AWS Secrets Manager (recommended)

### Network Security

- ✅ HTTPS for all API calls
- ✅ VPC endpoints for AWS services (optional)
- ✅ Security groups for Lambda (if in VPC)

### Compliance

- ✅ CloudTrail logging enabled
- ✅ AWS Config for compliance monitoring
- ✅ Regular security assessments

---

## 💰 Cost Optimization

### Estimated Monthly Costs

| Service | Usage | Estimated Cost |
|---------|-------|----------------|
| Bedrock (Nova Pro) | 1M tokens | $8-15 |
| OpenSearch Serverless | 1 OCU | $700 |
| S3 | 10GB storage | $0.23 |
| Lambda | 1M requests | $0.20 |
| **Total** | | **~$708-715/month** |

### Cost Reduction Tips

1. **Use On-Demand for Development**
   - Only pay for what you use
   - No upfront commitments

2. **Optimize OpenSearch**
   - Use minimum OCU capacity
   - Delete unused collections
   - Consider alternatives for dev/test

3. **Monitor Usage**
   ```bash
   aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31
   ```

4. **Set Budget Alerts**
   - Configure AWS Budgets
   - Get notified at thresholds

5. **Clean Up Regularly**
   ```bash
   python cleanup.py  # When not in use
   ```

6. **Use Provisioned Throughput** (Production)
   - Lower per-token costs
   - Predictable pricing

---

## 🤝 Contributing

We welcome contributions! Here's how:

### 1. Fork the Repository

```bash
git fork <repository-url>
```

### 2. Create Feature Branch

```bash
git checkout -b feature/amazing-feature
```

### 3. Make Changes

- Follow existing code style
- Add tests for new features
- Update documentation

### 4. Test Thoroughly

```bash
python main.py deploy
python main.py test "test query"
```

### 5. Submit Pull Request

- Clear description of changes
- Reference any related issues
- Include screenshots if UI changes

### Development Guidelines

- **Code Style**: Follow PEP 8
- **Documentation**: Update README for new features
- **Testing**: Add unit tests
- **Commits**: Use conventional commits

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Amazon Bedrock Team** - For the incredible AI platform
- **AWS** - For robust cloud infrastructure
- **Streamlit** - For the intuitive UI framework
- **Open Source Community** - For inspiration and support

---

## 📧 Support

### Getting Help

1. **Documentation**: Check this README and `data/` docs
2. **Issues**: Open a GitHub issue
3. **AWS Support**: For platform-specific issues
4. **Community**: Join discussions

### Useful Links

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Amazon Nova Models](https://aws.amazon.com/bedrock/nova/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)

---

## 🚀 What's Next?

### Planned Features

- [ ] Add more specialized agents (Translation, Summarization, etc.)
- [ ] Implement conversation memory and context
- [ ] Add user authentication and authorization
- [ ] Deploy to production with CI/CD
- [ ] Add monitoring dashboards (CloudWatch, Grafana)
- [ ] Implement A/B testing for agent performance
- [ ] Add voice interface support
- [ ] Multi-language support
- [ ] Advanced analytics and insights

### Roadmap

**Q1 2026**
- Enhanced agent collaboration
- Improved RAG performance
- Additional data source connectors

**Q2 2026**
- Production deployment templates
- Advanced monitoring and alerting
- Performance optimization

---

## 📊 Project Stats

- **Lines of Code**: ~3,000+
- **AWS Services**: 7 (Bedrock, Lambda, S3, OpenSearch, IAM, CloudWatch, STS)
- **Agents**: 4 (1 Supervisor + 3 Collaborators)
- **Supported Models**: 3+ foundation models
- **Deployment Time**: ~10-15 minutes

---

<div align="center">

**Built with ❤️ using Amazon Bedrock, Python, and AWS**

⭐ Star this repo if you find it helpful!

[Report Bug](https://github.com/your-repo/issues) · [Request Feature](https://github.com/your-repo/issues) · [Documentation](https://github.com/your-repo/wiki)

</div>