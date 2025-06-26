# Dual Personality AI Agent Project Summary

## Project Overview

**Goal**: Create a dual-personality AI agent that can respond in the style of NetworkChuck (technology/networking) and Bloomy (finance/Excel) using video transcripts as training data.

**Architecture**: RAG (Retrieval-Augmented Generation) system with personality-specific context retrieval.

---

## Current Status ✅

### Dataset Prepared
- **Total Videos**: 62 videos
  - **NetworkChuck**: 30 videos (technology/networking content)
  - **Bloomy**: 32 videos (finance/Excel content)
- **Enhanced metadata**: Categories, difficulty levels, key topics, priority ratings
- **Video URLs**: Verified and corrected for actual channel content

### Technology Stack
- **Transcription**: OpenAI Whisper (small model selected)
- **Processing**: Python with yt-dlp for audio extraction
- **Expected Processing Time**: ~10 hours for complete dataset
- **Output Format**: JSON files + CSV files with personality metadata

### Files Ready
- `enhanced_video_dataset.json` - Complete video dataset with metadata
- `whisper_youtube_extractor.py` - Updated processor with dual personality support

---

## NetworkChuck Video Categories (30 videos)

### Linux & Command Line (6 videos)
- 60 Linux Commands tutorial
- Linux for Hackers series
- Ansible automation
- PowerShell in Linux

### Cloud Computing & Containers (8 videos)
- Docker fundamentals and networking
- Kubernetes orchestration
- AWS basics and deployment
- Terraform infrastructure

### Networking Fundamentals (5 videos)
- DNS and subnetting
- Internet infrastructure
- Wireshark analysis
- pfSense router setup

### Cybersecurity & Hacking (6 videos)
- Password cracking with Kali Linux
- Network scanning with Nmap
- ProxyChains for anonymity
- USB security threats

### VPN & Security (2 videos)
- Free VPN server setup in AWS
- VPN alternatives and security

### Programming (3 videos)
- Python fundamentals
- GitHub Actions CI/CD
- Script automation

### Hardware & Infrastructure (3 videos)
- Raspberry Pi projects
- Pi-hole DNS filtering
- GPS tracking systems

### Virtualization (2 videos)
- Virtual machines setup
- Proxmox vs VMware

### Tools & Utilities (1 video)
- Windows Terminal optimization

---

## Bloomy Video Categories (32 videos)

### Bloomberg Terminal (9 videos)
- Terminal basics and navigation
- Function guides and shortcuts
- API integration
- Equity and fixed income analysis

### Excel Advanced (11 videos)
- Advanced functions and formulas
- Power Query and Power Pivot
- VBA automation
- Dynamic arrays

### Excel Fundamentals (4 videos)
- VLOOKUP and INDEX/MATCH
- Data validation
- Conditional formatting
- Basic functions

### Financial Analysis (8 videos)
- Financial modeling
- Risk management
- Portfolio analysis
- Options and bond pricing

---

## Technical Implementation

### Whisper Model Selection
- **Model**: `small`
- **Rationale**: Best balance for NetworkChuck's technical content
  - Fast-paced delivery with technical jargon
  - Acronyms and command-line instructions
  - Better accuracy than `base`, faster than `medium`
- **Processing Time**: ~10 minutes per video

### Directory Structure
```
data/
├── transcript_cache/
│   ├── networkchuck/     # NetworkChuck JSON files
│   └── bloomy/           # Bloomy JSON files
├── transcript_csv/
│   ├── networkchuck/     # NetworkChuck CSV files
│   └── bloomy/           # Bloomy CSV files
├── audio_cache/          # Temporary audio files
└── logs/                 # Processing logs
```

### Output Format
Each transcript includes:
- **Video metadata**: Title, uploader, duration, upload date
- **Personality data**: Domain, expertise areas, difficulty
- **Transcript segments**: Text with timestamps
- **Processing metadata**: Model used, processing time

---

## Immediate Next Steps

### 1. Launch Transcription Process
```bash
# Clear existing folders
rm -rf data/transcript_cache/*
rm -rf data/transcript_csv/*

# Launch processing (close other applications first)
python whisper_youtube_extractor.py
```

### Pre-processing Checklist
- ✅ Close Chrome/browsers (save RAM)
- ✅ Close streaming applications (save bandwidth)  
- ✅ Keep laptop plugged in (10+ hour process)
- ✅ Consider running overnight
- ✅ Verify enhanced_video_dataset.json exists

---

## Phase 1: Vector Database Creation

### Steps
1. **Choose embedding model**
   - Options: OpenAI embeddings, Sentence-BERT, others
   - Consider: Cost, accuracy, local vs API

2. **Create vector database**
   - Process transcript CSVs into vectors
   - Maintain personality metadata
   - Implement efficient retrieval

3. **Build retrieval system**
   - Personality-specific filtering
   - Semantic search capabilities
   - Context ranking and selection

4. **Test RAG pipeline**
   - Sample queries across personalities
   - Verify correct context retrieval
   - Measure response quality

---

## Phase 2: Documentation Enhancement

### Objective
Augment video transcripts with official documentation for comprehensive knowledge base.

### Implementation
1. **Create document_embedder.py**
   - Web scraping capabilities
   - PDF processing for documentation
   - Same vector format as transcripts

2. **Documentation Sources**

   **NetworkChuck Topics:**
   - Docker: docs.docker.com
   - Kubernetes: kubernetes.io/docs  
   - AWS: docs.aws.amazon.com
   - Linux: ubuntu.com/docs, linux.org
   - Networking: Cisco docs, IETF RFCs

   **Bloomy Topics:**
   - Bloomberg Terminal: bloomberg.com/professional/support
   - Excel: docs.microsoft.com/excel
   - Financial Modeling: CFA Institute materials

3. **Unified Vector Database**
   - Combine video transcripts + documentation
   - Enhanced metadata schema
   - Cross-reference capabilities

### Metadata Structure
```json
{
  "content": "text content",
  "source_type": "video_transcript" | "official_docs",
  "personality": "networkchuck" | "bloomy" | "officia