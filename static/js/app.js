class F1MultilingualChatBot {
    constructor() {
        this.chatMessages = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.loading = document.getElementById('loading');
        this.loadingText = document.getElementById('loading-text');
        this.languageDetection = document.getElementById('language-detection');
        this.detectedLangText = document.getElementById('detected-lang-text');

        this.initEventListeners();
    }

    initEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Auto-hide language detection after typing
        this.userInput.addEventListener('input', () => {
            this.languageDetection.style.display = 'none';
        });
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addMessage(message, 'user');

        // Clear input and show loading
        this.userInput.value = '';
        this.setLoading(true);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            if (response.ok) {
                // Show language detection
                this.showLanguageDetection(data.language);

                // Add bot response
                this.addMessage(data.answer, 'bot', {
                    sources: data.sources,
                    language: data.language,
                    retrievedDocs: data.retrieved_docs
                });
            } else {
                this.addMessage(data.error || 'Sorry, something went wrong.', 'bot');
            }
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        } finally {
            this.setLoading(false);
        }
    }

    addMessage(content, sender, metadata = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const senderLabel = sender === 'user' ?
            '<strong>You | आप:</strong>' :
            '<strong>🏎️ F1 Assistant:</strong>';

        let messageHTML = `
            <div class="message-content">
                ${senderLabel}
                ${this.formatMessage(content)}
            </div>
        `;

        // Add metadata for bot messages
        if (sender === 'bot' && metadata) {
            messageHTML += this.formatMetadata(metadata);
        }

        messageDiv.innerHTML = messageHTML;
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Convert newlines to <br> tags and handle multilingual content
        return content.replace(/\n/g, '<br>');
    }

    formatMetadata(metadata) {
        let metadataHTML = '';

        // Add language indicator
        if (metadata.language) {
            const langName = metadata.language === 'hi' ? 'हिंदी' : 'English';
            const langFlag = metadata.language === 'hi' ? '🇮🇳' : '🇬🇧';

            metadataHTML += `
                <div class="language-info" style="margin-top: 10px; font-size: 0.85em; color: #666;">
                    <i class="fas fa-globe"></i> Response in ${langFlag} ${langName}
                </div>
            `;
        }

        // Add sources
        if (metadata.sources && metadata.sources.length > 0) {
            metadataHTML += '<div class="message-sources">';
            metadataHTML += '<strong><i class="fas fa-book"></i> Sources | स्रोत:</strong><br>';

            metadata.sources.forEach(source => {
                const sourceText = this.formatSource(source);
                metadataHTML += `<span class="source-item" title="${source.url}">${sourceText}</span>`;
            });

            metadataHTML += '</div>';
        }

        // Add retrieved docs count
        if (metadata.retrievedDocs) {
            metadataHTML += `
                <div class="retrieval-info" style="margin-top: 8px; font-size: 0.8em; color: #999;">
                    <i class="fas fa-search"></i> Found ${metadata.retrievedDocs} relevant sources
                </div>
            `;
        }

        return metadataHTML;
    }

    formatSource(source) {
        let sourceText = source.title || 'F1 Information';

        if (source.source) {
            sourceText = `${source.source}: ${sourceText}`;
        }

        if (source.section) {
            sourceText += ` (${source.section})`;
        }

        return sourceText;
    }

    showLanguageDetection(language) {
        const langName = language === 'hi' ? 'हिंदी (Hindi)' : 'English';
        const langFlag = language === 'hi' ? '🇮🇳' : '🇬🇧';

        this.detectedLangText.textContent = `${langFlag} Language detected: ${langName}`;
        this.languageDetection.style.display = 'block';

        // Hide after 3 seconds
        setTimeout(() => {
            this.languageDetection.style.display = 'none';
        }, 3000);
    }

    setLoading(show) {
        this.loading.style.display = show ? 'block' : 'none';
        this.sendBtn.disabled = show;
        this.userInput.disabled = show;

        if (show) {
            // Animate loading text
            const loadingTexts = [
                'Processing your question... | आपके प्रश्न को संसाधित कर रहे हैं...',
                'Searching F1 database... | F1 डेटाबेस खोज रहे हैं...',
                'Generating response... | प्रतिक्रिया तैयार कर रहे हैं...'
            ];

            let textIndex = 0;
            this.loadingInterval = setInterval(() => {
                this.loadingText.textContent = loadingTexts[textIndex];
                textIndex = (textIndex + 1) % loadingTexts.length;
            }, 1500);
        } else {
            if (this.loadingInterval) {
                clearInterval(this.loadingInterval);
            }
        }
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Global function for example questions
function setQuestion(question) {
    const userInput = document.getElementById('user-input');
    userInput.value = question;
    userInput.focus();

    // Add subtle animation
    userInput.style.transform = 'scale(1.02)';
    setTimeout(() => {
        userInput.style.transform = 'scale(1)';
    }, 200);
}

// Initialize chatbot when page loads
document.addEventListener('DOMContentLoaded', () => {
    new F1MultilingualChatBot();

    // Add some flair to example questions
    const exampleQuestions = document.querySelectorAll('.example-question');
    exampleQuestions.forEach((question, index) => {
        question.style.animationDelay = `${index * 0.1}s`;
        question.classList.add('animate__animated', 'animate__fadeInUp');
    });
});

// Add CSS animation classes if not using animate.css
if (!document.querySelector('link[href*="animate"]')) {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .animate__animated {
            animation-duration: 0.5s;
            animation-fill-mode: both;
        }

        .animate__fadeInUp {
            animation-name: fadeInUp;
        }
    `;
    document.head.appendChild(style);
}
