"""
Gradio UI for Music Knowledge Graph Chatbot.

Simple and compatible with Gradio 6.x
"""

import os
import re
import logging
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)

# Global state for chatbot
_chatbot = None
_retriever = None


def set_chatbot(chatbot, retriever=None):
    """Set the chatbot and retriever instances."""
    global _chatbot, _retriever
    _chatbot = chatbot
    _retriever = retriever


def generate_demo_response(message: str) -> str:
    """Generate demo response when no model is loaded."""
    message_lower = message.lower()
    
    responses = {
        'taylor swift': "Taylor Swift is an American singer-songwriter known for pop and country music. She has released albums like '1989', 'Red', 'Folklore', and 'Midnights'.",
        'ed sheeran': "Ed Sheeran is a British singer-songwriter. His popular albums include '+', 'x', '÷', and '='.",
        'genre': "I can help you find information about music genres! Popular genres include Pop, Rock, Hip-Hop, R&B, Country, Jazz, and Electronic.",
        'album': "I can tell you about albums! What specific album or artist are you interested in?",
        'song': "I'd be happy to help with song information! Which song or artist would you like to know about?",
        'bts': "BTS (방탄소년단) is a South Korean boy band formed in 2013. Members include RM, Jin, Suga, J-Hope, Jimin, V, and Jungkook.",
        'beyoncé': "Beyoncé is an American singer and actress. She has won numerous Grammy awards.",
        'beyonce': "Beyoncé is an American singer and actress. She has won numerous Grammy awards.",
        'grammy': "The Grammy Awards are annual music awards presented by the Recording Academy.",
        'pop': "Pop music is a genre of popular music. Popular pop artists include Taylor Swift, Ed Sheeran, and Ariana Grande.",
        'rock': "Rock music is a broad genre that originated in the 1950s.",
        'hello': "Hello! I'm the Music Knowledge Graph Chatbot. Ask me about artists, albums, songs, or genres!",
        'hi': "Hi there! Ask me anything about music - artists, albums, songs, genres, and more!",
    }
    
    for keyword, response in responses.items():
        if keyword in message_lower:
            return response
    
    return """Welcome to the Music Knowledge Graph Chatbot! 🎵

I'm currently running in demo mode. Ask me about:
- Artists (Taylor Swift, Ed Sheeran, BTS, Beyoncé...)
- Albums and songs
- Music genres (Pop, Rock, Hip-Hop...)
- Grammy awards

Try asking: "What genre does Taylor Swift play?" """


def chat_respond(message: str, history: list) -> str:
    """Process message and return response."""
    if not message.strip():
        return ""
    
    try:
        if _chatbot is not None:
            if _retriever is not None:
                result = _chatbot.answer_with_graph_context(message, _retriever, max_hops=2)
                answer = result['answer']
            else:
                answer = _chatbot.generate(message)
            
            # Clean up thinking tags
            answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
        else:
            answer = generate_demo_response(message)
            
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        answer = f"Sorry, an error occurred. Please try again."
    
    return answer


def create_gradio_interface(chatbot=None, graph_retriever=None, share=False):
    """Create beautiful Gradio ChatInterface matching Figma design."""
    import gradio as gr
    
    # Set global state
    set_chatbot(chatbot, graph_retriever)
    
    # Get logo path if exists
    logo_path = os.path.join(os.path.dirname(__file__), "../../assets/figma/logo.svg")
    if not os.path.exists(logo_path):
        logo_path = None
    
    # Status message
    model_status = "✅ Model Loaded" if chatbot else "⚠️ Demo Mode"
    graph_status = "✅ Graph Connected" if graph_retriever else "⚠️ No Graph"
    
    # Custom CSS matching Figma design
    custom_css = """
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;700&family=DM+Sans:wght@400&display=swap');
    
    /* Main app container - White background with blur effects */
    .gradio-container,
    body,
    html {
        font-family: 'Manrope', 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
        min-height: 100vh !important;
        padding: 0 !important;
        position: relative !important;
        overflow-x: hidden !important;
    }
    
    /* Force white background everywhere */
    .dark,
    [data-theme="dark"],
    .gradio-container.dark {
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
    }
    
    /* Background blur effects */
    .gradio-container::before {
        content: '';
        position: fixed;
        top: 50px;
        left: 264px;
        width: 280px;
        height: 280px;
        background: #89BCFF;
        border-radius: 50%;
        filter: blur(300px);
        opacity: 0.6;
        z-index: 0;
        pointer-events: none;
    }
    
    .gradio-container::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 414px;
        height: 414px;
        background: #FF86E1;
        border-radius: 50%;
        filter: blur(500px);
        opacity: 0.5;
        z-index: 0;
        pointer-events: none;
    }
    
    /* Main content wrapper */
    main {
        max-width: 1280px !important;
        margin: 0 auto !important;
        padding: 0 !important;
        position: relative;
        z-index: 1;
    }
    
    /* Header section - centered with logo and title */
    header {
        background: transparent !important;
        padding: 164px 0 48px 0 !important;
        margin-bottom: 0 !important;
        text-align: center !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Logo styling */
    .logo-container {
        margin-bottom: 48px;
    }
    
    .logo-container img {
        width: 36px;
        height: 38px;
    }
    
    /* Title styling - "Ask our AI anything" */
    h1 {
        font-family: 'Manrope', sans-serif !important;
        font-weight: 400 !important;
        font-size: 24px !important;
        line-height: 1.366 !important;
        color: #160211 !important;
        text-align: center !important;
        margin: 0 !important;
        padding: 0 !important;
        background: none !important;
        -webkit-text-fill-color: #160211 !important;
    }
    
    /* Description text */
    .description, .description p, .description div {
        display: none !important;
    }
    
    /* Chatbot container */
    #component-0, 
    #chatbot,
    .chatbot,
    .gradio-chatbot,
    [id*="chatbot"],
    [class*="chatbot"] {
        background: transparent !important;
        background-color: transparent !important;
        border-radius: 0 !important;
        padding: 0 !important;
        box-shadow: none !important;
        border: none !important;
        min-height: auto !important;
    }
    
    /* Force white background for main content areas */
    main,
    .main,
    .container,
    .gradio-container > div {
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
    }
    
    /* Chat messages area */
    .chat-message, .message-wrap {
        margin-bottom: 15px !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* User message bubbles */
    .message.user, .user-message, [data-testid="user"] {
        background: #FFFFFF !important;
        color: #160211 !important;
        border-radius: 8px !important;
        padding: 10px !important;
        margin: 10px 0 !important;
        border: 1px solid #FFFFFF !important;
        max-width: fit-content !important;
        margin-left: auto !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        line-height: 1.302 !important;
    }
    
    /* Bot message bubbles */
    .message.bot, .message:not(.user), .bot-message, [data-testid="bot"] {
        background: #FFFFFF !important;
        color: #160211 !important;
        border-radius: 8px !important;
        padding: 10px !important;
        margin: 10px 0 !important;
        border: 1px solid #FFFFFF !important;
        max-width: fit-content !important;
        margin-right: auto !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        line-height: 1.302 !important;
    }
    
    /* Input box - matching Figma design */
    textarea, input[type="text"] {
        background: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid rgba(22, 2, 17, 0.3) !important;
        padding: 10px !important;
        font-family: 'Manrope', sans-serif !important;
        font-size: 14px !important;
        line-height: 1.366 !important;
        color: #56637E !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
        width: 100% !important;
    }
    
    textarea::placeholder, input[type="text"]::placeholder {
        color: #56637E !important;
        font-family: 'Manrope', sans-serif !important;
        opacity: 1 !important;
    }
    
    textarea:focus, input[type="text"]:focus {
        border-color: rgba(22, 2, 17, 0.5) !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Input container */
    .input-container {
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        background: #FFFFFF !important;
        border: 1px solid rgba(22, 2, 17, 0.3) !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    /* Submit button - Send icon */
    button[type="submit"], button.primary {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        cursor: pointer !important;
        box-shadow: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
    }
    
    button[type="submit"]:hover, button.primary:hover {
        transform: none !important;
        opacity: 0.8 !important;
    }
    
    button[type="submit"] svg, button.primary svg {
        width: 36px !important;
        height: 36px !important;
        fill: rgba(69, 98, 136, 0.5) !important;
    }
    
    /* Suggestions section */
    .suggestions-container {
        margin-top: 35px;
        padding: 0 222px;
    }
    
    .suggestions-title {
        font-family: 'Manrope', sans-serif !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        line-height: 1.366 !important;
        color: #56637E !important;
        margin-bottom: 15px !important;
    }
    
    .suggestions-grid {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        justify-content: flex-start;
    }
    
    /* Suggestion boxes */
    .suggestion-box {
        background: rgba(255, 255, 255, 0.5) !important;
        border: 1px solid #FFFFFF !important;
        border-radius: 8px !important;
        padding: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 400 !important;
        font-size: 14px !important;
        line-height: 1.302 !important;
        color: #160211 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .suggestion-box:hover {
        background: rgba(255, 255, 255, 0.8) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px !important;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.05) !important;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(0, 0, 0, 0.2) !important;
        border-radius: 4px !important;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Hide default Gradio elements */
    footer {
        display: none !important;
    }
    """
    
    # Create header HTML matching Figma design
    logo_html = ""
    if logo_path and os.path.exists(logo_path):
        logo_html = f'<img src="/file={logo_path}" alt="Logo" style="width: 36px; height: 38px;">'
    else:
        logo_html = '<div style="width: 36px; height: 38px; background: #160211; border-radius: 4px;"></div>'
    
    header_html = f"""
    <div style="display: flex; flex-direction: column; align-items: center; gap: 48px; padding: 164px 0 48px 0;">
        <div class="logo-container">
            {logo_html}
        </div>
        <h1 style="font-family: 'Manrope', sans-serif; font-weight: 400; font-size: 24px; line-height: 1.366; color: #160211; text-align: center; margin: 0;">
            Ask our AI anything
        </h1>
    </div>
    """
    
    # Wrap ChatInterface in Blocks to apply CSS properly
    with gr.Blocks(css=custom_css, title="Music Knowledge Graph Chatbot") as demo:
        # Create ChatInterface inside Blocks
        chat_interface = gr.ChatInterface(
            fn=chat_respond,
            title="",  # Empty title, we'll use custom header
            description=header_html,
            examples=[
                "What can I ask you to do?",
                "Which one of my projects is performing the best?",
                "What projects should I be concerned about right now?",
            ],
        )
        
        # Add custom JavaScript for suggestions and styling
        demo.load(
            js="""
            () => {
            
            setTimeout(() => {
                // Add suggestions section
                const chatbotContainer = document.querySelector('#component-0') || document.querySelector('[id*="chatbot"]');
                if (chatbotContainer && !document.querySelector('.suggestions-container')) {
                    const suggestionsHTML = `
                        <div class="suggestions-container" style="margin-top: 35px; padding: 0 222px; max-width: 1280px; margin-left: auto; margin-right: auto;">
                            <div class="suggestions-title" style="font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 14px; line-height: 1.366; color: #56637E; margin-bottom: 15px;">
                                Suggestions on what to ask Our AI
                            </div>
                            <div class="suggestions-grid" style="display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-start;">
                                <div class="suggestion-box" style="background: rgba(255, 255, 255, 0.5); border: 1px solid #FFFFFF; border-radius: 8px; padding: 10px; font-family: 'DM Sans', sans-serif; font-size: 14px; color: #160211; cursor: pointer; transition: all 0.2s ease;">
                                    What can I ask you to do?
                                </div>
                                <div class="suggestion-box" style="background: rgba(255, 255, 255, 0.5); border: 1px solid #FFFFFF; border-radius: 8px; padding: 10px; font-family: 'DM Sans', sans-serif; font-size: 14px; color: #160211; cursor: pointer; transition: all 0.2s ease;">
                                    Which one of my projects is performing the best?
                                </div>
                                <div class="suggestion-box" style="background: rgba(255, 255, 255, 0.5); border: 1px solid #FFFFFF; border-radius: 8px; padding: 10px; font-family: 'DM Sans', sans-serif; font-size: 14px; color: #160211; cursor: pointer; transition: all 0.2s ease;">
                                    What projects should I be concerned about right now?
                                </div>
                            </div>
                        </div>
                    `;
                    chatbotContainer.insertAdjacentHTML('afterend', suggestionsHTML);
                    
                    // Add click handlers for suggestions
                    document.querySelectorAll('.suggestion-box').forEach(box => {
                        box.addEventListener('click', function() {
                            const text = this.textContent.trim();
                            const textarea = document.querySelector('textarea');
                            if (textarea) {
                                textarea.value = text;
                                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                                textarea.focus();
                            }
                        });
                        
                        box.addEventListener('mouseenter', function() {
                            this.style.background = 'rgba(255, 255, 255, 0.8)';
                            this.style.transform = 'translateY(-2px)';
                        });
                        
                        box.addEventListener('mouseleave', function() {
                            this.style.background = 'rgba(255, 255, 255, 0.5)';
                            this.style.transform = 'translateY(0)';
                        });
                    });
                }
                
                // Update input placeholder
                const textarea = document.querySelector('textarea');
                if (textarea) {
                    textarea.placeholder = 'Ask me anything about your projects';
                }
            }, 500);
        }
        """
        )
    
    return demo


def launch_gradio(chatbot=None, graph_retriever=None, port=7860, share=False):
    """Launch the Gradio interface."""
    demo = create_gradio_interface(chatbot, graph_retriever, share)
    
    logger.info(f"🚀 Launching Gradio UI on http://localhost:{port}")
    print(f"\n🌐 Open http://localhost:{port} in your browser\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=share,
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Launch Music Chatbot Gradio UI")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--load-model", action="store_true")
    parser.add_argument("--lora-path", type=str, default=None)
    
    args = parser.parse_args()
    
    chatbot = None
    retriever = None
    
    if args.load_model:
        try:
            from src.models.qwen_model import Qwen3MusicChatbot
            print("Loading chatbot model...")
            chatbot = Qwen3MusicChatbot(
                model_name="Qwen/Qwen3-0.6B",
                lora_path=args.lora_path,
                quantization="4bit"
            )
            print("✅ Model loaded!")
        except Exception as e:
            print(f"⚠️ Could not load model: {e}")
    
    launch_gradio(chatbot, retriever, args.port, args.share)
