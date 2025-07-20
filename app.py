import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    base_url=os.getenv('OPENAI_BASE_URL', 'http://localhost:11434/v1'),
    api_key=os.getenv('OPENAI_API_KEY', 'ollama')
)
MODEL = os.getenv('MODEL', 'llama3.2')

# System message configuration
BASE_SYSTEM_MESSAGE = """You are a helpful assistant in a clothes store. You should try to gently encourage 
the customer to try items that are on sale. Hats are 60% off, and most other items are 50% off. 
For example, if the customer says 'I'm looking to buy a hat', 
you could reply something like, 'Wonderful - we have lots of hats - including several that are part of our sales event.'
Encourage the customer to buy hats if they are unsure what to get.

If the customer asks for shoes, you should respond that shoes are not on sale today, 
but remind the customer to look at hats!"""

BELT_ADDON = " The store does not sell belts; if you are asked for belts, be sure to point out other items on sale."

def get_system_message(user_message: str) -> str:
    """Generate appropriate system message based on user input."""
    system_msg = BASE_SYSTEM_MESSAGE
    if 'belt' in user_message.lower():
        system_msg += BELT_ADDON
    return system_msg

def chat(message: str, history: list) -> str:
    """
    Handle chat interaction with streaming response.
    
    Args:
        message: User's current message
        history: List of previous messages in format [{"role": "user/assistant", "content": "..."}]
    
    Yields:
        Partial responses as they're generated
    """
    try:
        # Build messages array with dynamic system message
        messages = [
            {"role": "system", "content": get_system_message(message)}
        ] + history + [
            {"role": "user", "content": message}
        ]

        # Create streaming chat completion
        stream = client.chat.completions.create(
            model=MODEL, 
            messages=messages, 
            stream=True,
            temperature=0.7,  # Add some personality
            max_tokens=500    # Reasonable limit for store assistant
        )

        response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                response += chunk.choices[0].delta.content
                yield response
                
    except Exception as e:
        error_msg = f"Sorry, I'm having trouble connecting right now. Error: {str(e)}"
        yield error_msg

def main():
    """Launch the Gradio interface."""
    interface = gr.ChatInterface(
        fn=chat,
        type="messages",
        title="🛍️ Clothes Store Assistant",
        description="Welcome to our store! I'm here to help you find great deals. Ask me about our items!",
        examples=[
            "What items do you have on sale?",
            "I'm looking for a hat",
            "Do you have any shoes?",
            "What should I buy today?"
        ],
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 800px !important;
            margin: auto !important;
        }
        """
    )
    
    interface.launch(
        server_name="0.0.0.0",  # Allow external access
        server_port=7860,       # Default Gradio port
        share=False,            # Set to True if you want public sharing
        debug=False             # Set to True for development
    )

if __name__ == "__main__":
    main()