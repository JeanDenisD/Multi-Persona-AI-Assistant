# Multi-Persona AI Assistant

> **Production-ready AI assistant with 6 distinct personalities, enhanced memory, and professional voice integration**

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-HuggingFace_Spaces-blue?style=for-the-badge)](https://huggingface.co/spaces/JeanDenisD/multi-persona-ai-assistant)
[![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)](https://python.org)
[![License](https://github.com/JeanDenisD/networkchuck-ai-chatbot-assistant?tab=MIT-1-ov-file)](LICENSE)

## 🎯 Overview

The Multi-Persona AI Assistant is a sophisticated multi-modal AI platform featuring 6 distinct expert personalities, each with unique knowledge domains, response styles, and voice characteristics. Built with advanced RAG (Retrieval-Augmented Generation) technology and enhanced conversation memory, it provides natural, context-aware interactions through both text and voice.

### ✨ Key Features

- 🎭 **6 AI Personalities**: NetworkChuck, Bloomy, DataScientist, StartupFounder, EthicalHacker, PatientTeacher
- 🧠 **Enhanced Memory**: 20-turn conversation window with intelligent auto-summarization
- 🎤🔊 **Voice Integration**: Bidirectional voice with personality-matched TTS/STT
- 📚 **Smart Knowledge Base**: 19,590 video transcript segments with semantic search
- 🎯 **Content Filtering**: User-controlled video/documentation inclusion
- 🔄 **Real-time Processing**: Sub-10s response times for both text and voice
- 🚀 **Production Ready**: Live deployment on HuggingFace Spaces

## 🎭 AI Personalities

| Personality           | Expertise                     | Response Style              | Voice Character          | Teaching Approach    |
| --------------------- | ----------------------------- | --------------------------- | ------------------------ | -------------------- |
| 🧔‍♂️ **NetworkChuck**   | Cybersecurity, Networking     | Energetic, uses analogies   | Enthusiastic mentor      | Hands-on, lively     |
| 👨‍💼 **Bloomy**         | Finance, Excel, Bloomberg     | Professional, structured    | Business analyst         | Clear, methodical    |
| 👩‍🔬 **DataScientist**  | Analytics, ML, Statistics     | Evidence-based, precise     | Research expert          | Analytical, thorough |
| 🤵 **StartupFounder** | Business, Scalability         | Pragmatic, growth-focused   | Entrepreneurial leader   | Practical, scalable  |
| 👩‍💻 **EthicalHacker**  | Security, Penetration Testing | Security-first, responsible | Cybersecurity specialist | Security-conscious   |
| 👩‍🏫 **PatientTeacher** | Education, Learning           | Patient, encouraging        | Supportive educator      | Patient, supportive  |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Gradio Interface                           │
│ 🎛️ Voice Controls │ 🎯 Filtering │ 🧪 Tests │ 🧠 Memory    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              NetworkChuck Chatbot                          │
│           Enhanced Memory + Voice Integration               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                SimplifiedRAG                               │
│   🤖 GPT-4o-mini   │   🔍 RAG Retriever   │   📚 Docs     │
└─────────┬───────────┬─────────────────────┬─────────────────┘
          │           │                     │
┌─────────▼──┐ ┌──────▼──────┐ ┌───────────▼────────────┐
│  Enhanced  │ │ElevenLabs + │ │    Pinecone Vector     │
│   Memory   │ │   Whisper   │ │   Database (19.5K      │
│ (20 turns) │ │ Voice I/O   │ │    segments)           │
└────────────┘ └─────────────┘ └────────────────────────┘
```

### 🔧 Technology Stack

**Core Technologies:**

- **AI/ML**: GPT-4o-mini, LangChain, OpenAI Embeddings
- **Voice**: ElevenLabs TTS/STT, Whisper (fallback)
- **Database**: Pinecone Vector Database
- **Interface**: Gradio with tabbed controls
- **Deployment**: HuggingFace Spaces

**Key Libraries:**

```
langchain>=0.1.0
openai>=1.0.0
pinecone-client>=3.0.0
elevenlabs>=0.2.0
gradio>=4.0.0
```

## 📊 Dataset & Knowledge Base

- **62 YouTube Videos** from tech education channels
- **19,590 Transcript Segments** with rich metadata
- **Semantic Search** via OpenAI embeddings
- **Smart Documentation** with context-aware matching
- **Video Timestamps** for precise source attribution

### Data Sources

- NetworkChuck (4.68M subscribers) - Cybersecurity, Networking
- ExplainHowToSimply (1.68K subscribers) - Technical tutorials
- Curated documentation links with semantic matching

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- ElevenLabs API key
- Pinecone API key

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/JeanDenisD/networkchuck-ai-assistant.git
cd networkchuck-ai-assistant
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your API keys:
# OPENAI_API_KEY=your_openai_key
# ELEVENLABS_API_KEY=your_elevenlabs_key
# PINECONE_API_KEY=your_pinecone_key
```

4. **Run the application**

```bash
python app.py
```

The interface will be available at `http://localhost:7860`

### 🐳 Docker Deployment

```bash
docker build -t networkchuck-ai .
docker run -p 7860:7860 --env-file .env networkchuck-ai
```

## 💡 Usage Examples

### Text Interaction

```python
# Ask NetworkChuck about Docker
user: "How do I set up Docker containers?"
networkchuck: "Hey there! 🚀 Docker containers are like coffee pods for your applications..."

# Switch to Bloomy for finance
user: "Explain VLOOKUP in Excel"
bloomy: "VLOOKUP is a powerful Excel function for data retrieval. Here's the structured approach..."
```

### Voice Interaction

1. **Record your question** using the microphone
2. **Select AI personality** (each has unique voice)
3. **Get spoken response** with clean, professional audio
4. **Conversation memory** maintains context across interactions

### Advanced Features

- **Content Filtering**: Toggle videos/docs inclusion
- **Memory Management**: 20-turn window with summarization
- **Test Suite**: Pre-built scenarios for testing
- **Response Tuning**: Adjust creativity and relevance

## 🎯 Key Improvements (v2.0)

| Feature             | Before (v1.0)        | After (v2.0)            | Impact                           |
| ------------------- | -------------------- | ----------------------- | -------------------------------- |
| **Memory**          | 10-turn truncation   | 20-turn + summarization | 2x context retention             |
| **AI Logic**        | Complex controller   | Natural GPT-4 reasoning | Eliminates false classifications |
| **Voice Quality**   | Asterisks in speech  | Clean audio processing  | Professional TTS output          |
| **Response Format** | 200+ word paragraphs | 50-150 words + bullets  | 3x more scannable                |
| **Architecture**    | Over-engineered      | Simple, maintainable    | Future-proof design              |

## 📁 Project Structure

```
networkchuck-ai-assistant/
├── app.py                          # Main Gradio application
├── src/
│   ├── core/
│   │   ├── chatbot.py             # Main chatbot orchestrator
│   │   ├── voice_manager.py       # Voice I/O handling
│   │   └── doc_matcher.py         # Smart documentation matching
│   ├── chains/
│   │   └── simplified_rag.py      # Enhanced RAG with GPT-4o-mini
│   ├── prompts/
│   │   └── personality_prompts.py # 6 personality definitions
│   └── utils/
│       └── voice_cleaner.py       # Clean TTS text processing
├── data/
│   ├── test_cases.json           # Test scenarios
│   └── official_docs/            # Documentation database
├── requirements.txt              # Python dependencies
├── .env.example                 # Environment template
└── README.md                   # This file
```

## 🧪 Testing

The project includes comprehensive testing for:

- **Personality Consistency**: Each AI maintains unique characteristics
- **Memory Functionality**: Context preservation across conversations
- **Voice Quality**: Clean TTS without formatting artifacts
- **Response Performance**: Sub-30s response times
- **Integration**: All components working together

Run tests:

```bash
python -m pytest tests/
python src/core/chatbot.py  # Integration test
```

## 🚀 Deployment

### HuggingFace Spaces (Current)

- **Live Demo**: [Try it now!](https://huggingface.co/spaces/JeanDenisD/networkchuck-and-bloomy-persona-chatbot)
- **Auto-scaling**: Handles multiple concurrent users
- **Zero-config**: No setup required for users

### Local Development

```bash
python app.py
# Access at http://localhost:7860
```

### Production Considerations

- Set appropriate API rate limits
- Monitor token usage (OpenAI/ElevenLabs)
- Scale Pinecone index for larger datasets
- Implement user authentication if needed

## 📈 Performance Metrics

- ⚡ **Response Time**: < 30 seconds (text and voice)
- 🧠 **Memory**: 20-turn conversation window
- 🎯 **Accuracy**: Context-aware responses with source attribution
- 🔊 **Voice Quality**: Professional TTS with personality matching
- 📊 **Scale**: 19,590 knowledge segments, 6 personalities

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Submit a pull request with detailed description

### Areas for Contribution

- Additional AI personalities
- New voice processing features
- Enhanced memory algorithms
- UI/UX improvements
- Documentation and tutorials

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **NetworkChuck** for inspiring educational content
- **OpenAI** for GPT-4o-mini and embeddings
- **ElevenLabs** for professional voice synthesis
- **Pinecone** for scalable vector database
- **HuggingFace** for seamless deployment platform

## 📞 Support & Contact

- **Live Demo**: [HuggingFace Spaces](https://huggingface.co/spaces/JeanDenisD/multi-persona-ai-assistant)
- **Issues**: [GitHub Issues](https://github.com/JeanDenisD/multi-persona-ai-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/JeanDenisD/multi-persona-ai-assistant/discussions)

---

<div align="center">

**Built with ❤️ by [Jean-Denis DRANE](https://github.com/JeanDenisD)**

_Making AI accessible through natural conversation_

[![Star this repo](https://img.shields.io/github/stars/JeanDenisD/networkchuck-ai-assistant?style=social)](https://github.com/JeanDenisD/multi-persona-ai-assistant/discussions)
[![Follow on GitHub](https://img.shields.io/github/followers/JeanDenisD?style=social)](https://github.com/JeanDenisD)

</div>
