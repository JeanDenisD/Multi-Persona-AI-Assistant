"""
Voice Text Cleaner - Remove formatting and asterisks for natural TTS
"""

import re


def clean_text_for_voice(text: str) -> str:
    """
    Clean text for TTS by removing formatting, asterisks, and non-speech elements
    """
    if not text:
        return ""
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic* -> italic
    text = re.sub(r'_(.*?)_', r'\1', text)        # _italic_ -> italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # `code` -> code
    
    # Remove standalone asterisks and formatting symbols
    text = re.sub(r'\*+', '', text)               # Remove any remaining asterisks
    text = re.sub(r'#+\s*', '', text)             # Remove # headers
    text = re.sub(r'-+\s*', '', text)             # Remove bullet dashes
    text = re.sub(r'•\s*', '', text)              # Remove bullet points
    
    # Remove URLs and links
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url) -> text
    
    # Remove video and documentation section headers
    text = re.sub(r'🎥.*?Source Videos?:.*?\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'📚.*?Documentation:.*?\n', '', text, flags=re.MULTILINE)
    
    # Remove emoji and special characters that sound awkward
    text = re.sub(r'[🎥📚🎯🔧⚙️✅❌🚀💡📊🎭🧠🔍📄🎤🔊]', '', text)
    
    # Remove numbered/bulleted lists formatting
    text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)  # 1. item -> item
    text = re.sub(r'^\s*[-•]\s*', '', text, flags=re.MULTILINE)  # - item -> item
    
    # Clean up extra whitespace
    text = re.sub(r'\n+', ' ', text)              # Multiple newlines -> single space
    text = re.sub(r'\s+', ' ', text)              # Multiple spaces -> single space
    text = text.strip()
    
    return text


def extract_voice_content(response_text: str) -> str:
    """
    Extract only the main content suitable for voice, removing sections
    """
    if not response_text:
        return ""
    
    lines = response_text.split('\n')
    voice_lines = []
    skip_section = False
    
    for line in lines:
        # Skip video and documentation sections
        if any(marker in line for marker in ['🎥', 'Source Videos:', '📚', 'Documentation:', 'Related Documentation:']):
            skip_section = True
            continue
        
        # Reset skip when we hit a new section or normal content
        if line.strip() and not line.startswith('•') and not line.startswith('-') and not line.startswith('**['):
            skip_section = False
        
        # Only include main content lines
        if not skip_section and line.strip():
            voice_lines.append(line)
    
    # Join and clean the voice content
    voice_text = '\n'.join(voice_lines)
    cleaned_text = clean_text_for_voice(voice_text)
    
    return cleaned_text


def test_voice_cleaning():
    """Test the voice text cleaning functionality"""
    
    test_texts = [
        "**Docker** is a *containerization* platform that lets you package applications.",
        "Here's how to secure your network:\n• Use strong passwords\n• Enable firewall\n• Update regularly",
        "Check out this video: [Docker Tutorial](https://youtube.com/watch?v=123) for more info.",
        "🎥 **Source Videos:**\n1. **[Docker Basics](https://example.com)**\n• 5:30\n\nDocker is amazing! *Really* **powerful** stuff.",
        "```bash\necho 'Hello World'\n```\nThis command prints text with **formatting** and *emphasis*.",
    ]
    
    print("🧪 Testing Voice Text Cleaning")
    print("=" * 50)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}:")
        print(f"Original: {text}")
        cleaned = clean_text_for_voice(text)
        print(f"Cleaned:  {cleaned}")
        print(f"Asterisks removed: {'*' not in cleaned}")
    
    print("\n✅ Voice cleaning tests completed!")


if __name__ == "__main__":
    test_voice_cleaning()