# Knowledge Base Sample Data

This directory contains sample documents for the Amazon Bedrock Knowledge Base implementation.

## Overview

The knowledge base uses these documents to provide context-aware responses through RAG (Retrieval Augmented Generation). Documents are uploaded to S3, converted to vector embeddings, and stored in Amazon OpenSearch Serverless for semantic search.

## Sample Documents

### 1. sample_kb_data.txt
**Purpose:** Main system documentation  
**Content:** Comprehensive overview of the multi-agent system including:
- System architecture and components
- Available agents (Weather, Stock, News)
- AWS services used
- Foundation models
- Multi-agent collaboration patterns
- Knowledge base integration
- Use cases and examples
- Best practices
- Troubleshooting guide
- Security considerations
- Performance optimization

**Use Cases:**
- "How does the multi-agent system work?"
- "What agents are available?"
- "How do I use the weather agent?"
- "What AWS services does this use?"

### 2. agent_capabilities.txt
**Purpose:** Detailed agent capabilities and examples  
**Content:** In-depth information about each agent:
- Weather Agent features and query examples
- Stock Agent capabilities and usage
- News Agent functionality
- Multi-agent collaboration examples
- Integration patterns
- Error handling
- Performance metrics
- Future enhancements

**Use Cases:**
- "What can the weather agent do?"
- "Show me examples of stock queries"
- "How do I ask multi-agent questions?"
- "What are the response times?"

### 3. aws_bedrock_guide.txt
**Purpose:** Technical guide for Amazon Bedrock  
**Content:** Comprehensive Bedrock documentation:
- Introduction to Amazon Bedrock
- Available foundation models
- Bedrock Agents architecture
- Multi-agent collaboration modes
- Knowledge bases setup
- IAM permissions required
- Best practices
- Monitoring and debugging
- Cost optimization
- Common use cases
- Integration patterns
- Troubleshooting guide
- Advanced features

**Use Cases:**
- "What is Amazon Bedrock?"
- "What foundation models are available?"
- "How do I set up a knowledge base?"
- "What IAM permissions do I need?"

### 4. faq.txt
**Purpose:** Frequently asked questions  
**Content:** Q&A format covering:
- General questions about the system
- Setup and configuration
- Agent questions
- Knowledge base questions
- Usage questions
- Troubleshooting
- Performance optimization
- Cost management
- Security
- Customization
- Maintenance
- Advanced topics
- Integration options
- Support resources

**Use Cases:**
- "How do I deploy the system?"
- "What are the prerequisites?"
- "How do I add more agents?"
- "How much does this cost?"

## Document Format

All documents are in plain text format (.txt) for optimal compatibility with the knowledge base. They include:
- Clear section headers
- Structured content
- Examples and use cases
- Technical details
- Best practices
- Troubleshooting tips

## Adding Your Own Documents

To add custom documents to the knowledge base:

1. **Create Your Document:**
   ```bash
   # Supported formats: TXT, PDF, DOCX, HTML, MD
   touch data/my_custom_doc.txt
   ```

2. **Add Content:**
   - Use clear section headers
   - Include relevant keywords
   - Provide examples
   - Keep content focused

3. **Upload to Knowledge Base:**
   ```bash
   # The system will automatically upload during deployment
   python main.py
   ```

4. **Sync Knowledge Base:**
   ```bash
   # Or sync manually if already deployed
   python -c "from orchestrator import MultiAgentOrchestrator; orch = MultiAgentOrchestrator(); orch.sync_knowledge_base()"
   ```

## Document Best Practices

### Content Structure
- Use clear, descriptive headers
- Break content into logical sections
- Include examples and use cases
- Provide step-by-step instructions where applicable

### Formatting
- Use consistent formatting throughout
- Keep paragraphs concise
- Use bullet points for lists
- Include code examples in code blocks

### Keywords
- Include relevant technical terms
- Use common query phrases
- Add synonyms for important concepts
- Include product names and versions

### Size Considerations
- Keep individual files under 50MB
- Split large documents into smaller files
- Use one topic per document when possible
- Avoid duplicate content across files

## Knowledge Base Query Examples

Once documents are in the knowledge base, you can query them:

```python
# Example queries that will use the knowledge base
"How does the multi-agent system work?"
"What are the available foundation models?"
"How do I troubleshoot agent errors?"
"What are the best practices for knowledge bases?"
"How much does this system cost to run?"
```

## Updating Documents

To update existing documents:

1. **Modify the Document:**
   ```bash
   # Edit your document
   nano data/sample_kb_data.txt
   ```

2. **Re-sync Knowledge Base:**
   ```bash
   # Sync to update embeddings
   python main.py --sync-only
   ```

3. **Verify Updates:**
   ```bash
   # Test queries to confirm updates
   streamlit run streamlit_app.py
   ```

## Document Metadata

The knowledge base automatically extracts metadata:
- File name
- File type
- Upload timestamp
- Document size
- Section headers

This metadata can be used for filtering and relevance ranking.

## Monitoring Document Usage

Track which documents are being retrieved:

1. **CloudWatch Logs:**
   - Check knowledge base query logs
   - Review retrieval scores
   - Monitor query patterns

2. **Streamlit App:**
   - Enable debug mode
   - View retrieved documents
   - Check relevance scores

## Troubleshooting

### Documents Not Being Retrieved

**Problem:** Queries don't return expected documents  
**Solutions:**
- Verify documents are uploaded to S3
- Check knowledge base sync status
- Review retrieval configuration
- Adjust similarity threshold
- Add more relevant keywords

### Low Relevance Scores

**Problem:** Retrieved documents have low relevance  
**Solutions:**
- Improve document content quality
- Add more specific examples
- Use clearer section headers
- Include common query phrases
- Reduce document size

### Sync Failures

**Problem:** Knowledge base sync fails  
**Solutions:**
- Check S3 bucket permissions
- Verify OpenSearch collection status
- Review CloudWatch logs
- Ensure documents are in supported formats
- Check file sizes

## Advanced Features

### Metadata Filtering
Add custom metadata to documents for filtering:
```json
{
  "category": "technical",
  "version": "1.0",
  "audience": "developers"
}
```

### Chunking Strategy
Documents are automatically chunked for optimal retrieval:
- Default chunk size: 300 tokens
- Overlap: 20% between chunks
- Configurable in knowledge base settings

### Hybrid Search
Combine semantic and keyword search:
- Semantic: Vector similarity
- Keyword: BM25 ranking
- Hybrid: Weighted combination

## Resources

- [AWS Bedrock Knowledge Bases Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [OpenSearch Serverless Documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)
- [RAG Best Practices](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-best-practices.html)

## Support

For issues with the knowledge base:
1. Check TROUBLESHOOTING.md in the project root
2. Review CloudWatch logs
3. Run diagnose.py for system status
4. Contact AWS support if needed

---

**Note:** These sample documents are provided as examples. Customize them for your specific use case and add your own domain-specific content for best results.