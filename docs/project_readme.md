# NetworkChuck AI Assistant 🤖

An intelligent chatbot that answers IT questions using NetworkChuck's YouTube content through RAG (Retrieval Augmented Generation) and LangChain agents.

## 🎯 Project Overview

This multimodal AI chatbot processes NetworkChuck's educational IT content to provide instant, accurate answers to technology questions. Built with modern AI stack including LangChain, Pinecone, and deployed on HuggingFace Spaces.

## 🚀 Live Demo

**[Try the Bot Here](https://huggingface.co/spaces/YOUR_USERNAME/networkchuck-ai)**

## ✨ Features

- **Intelligent Q&A**: Ask questions about networking, cybersecurity, cloud computing, Linux
- **Source Attribution**: Get answers with video references and timestamps
- **Conversational Memory**: Maintains context across chat sessions
- **Real-time Processing**: Fast responses with Pinecone vector search
- **Production Monitoring**: LangSmith integration for performance tracking

## 🛠️ Tech Stack

- **Frontend**: Gradio ChatInterface
- **Backend**: LangChain Agents + Tools
- **Vector Database**: Pinecone
- **LLM**: OpenAI GPT-3.5/4
- **Monitoring**: LangSmith
- **Deployment**: HuggingFace Spaces
- **Data Source**: NetworkChuck YouTube Channel

## 🏗️ Architecture

```
User Query → Gradio Interface → LangChain Agent → Pinecone Search → OpenAI LLM → Response
                                      ↓
                                LangSmith Monitoring
```

## 📊 Current Data

- **Videos Processed**: 15 NetworkChuck videos
- **Topics Covered**: Networking, Security, Cloud, Linux, Hardware
- **Vector Embeddings**: ~5,000 text chunks
- **Average Response Time**: <5 seconds

## 🔧 Local Development

### Prerequisites
```bash
Python 3.8+
pip install -r requirements.txt
```

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
LANGSMITH_API_KEY=your_langsmith_key
PINECONE_ENVIRONMENT=your_pinecone_env
```

### Run Locally
```bash
python app.py
```

## 📚 Usage Examples

**Networking Questions:**
- "How do I set up a VPN on my router?"
- "Explain the difference between TCP and UDP"
- "What is subnetting and how does it work?"

**Security Questions:**
- "How to secure a home network?"
- "What are the best practices for password management?"
- "How does a firewall work?"

**Cloud & Linux:**
- "How to deploy a web server on AWS?"
- "Basic Linux commands for beginners"
- "Docker vs Virtual Machines explained"

## 🎯 Future Improvements

- [ ] Add speech-to-text for voice queries
- [ ] Expand to 100+ videos
- [ ] Multi-language support
- [ ] Video timestamp integration
- [ ] Mobile app development

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- NetworkChuck for excellent IT educational content
- LangChain team for the amazing framework
- OpenAI for powerful language models
- Pinecone for vector database infrastructure

## 📞 Contact

**Your Name** - your.email@example.com
Project Link: https://github.com/yourusername/networkchuck-ai