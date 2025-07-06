import streamlit as st
import json
import os
import shutil
from datetime import datetime
import dotenv
from PIL import Image
from character_utils import CharacterManager
from api_handler import OpenRouterAPI

# Load environment variables from .env file
dotenv.load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Character Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: flex-start;
    color: #ffffff;
}
.user-message {
    background-color: #2c3e50;
    margin-left: 2rem;
    color: #ffffff;
}
.character-message {
    background-color: #3498db;
    margin-right: 2rem;
    color: #ffffff;
}
.message-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    margin-right: 1rem;
    object-fit: cover;
    border: 2px solid #ffffff;
}
.character-info {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    color: #333333;
}
.stButton > button {
    width: 100%;
}
/* Fix for white text in messages */
.chat-message strong {
    color: #ffffff;
    font-weight: bold;
}
.chat-message span {
    color: #ffffff;
}
/* Style for emphasized text */
.chat-message em {
    color: #444444;
    font-style: italic;
    background-color: rgba(255, 255, 255, 0.7);
    padding: 0 3px;
    border-radius: 3px;
}
.memory-item {
    background-color: #f0f0f0;
    padding: 8px;
    border-radius: 8px;
    margin-bottom: 5px;
    border-left: 3px solid #3498db;
}
.edit-character-form {
    background-color: #f9f9f9;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
}
.persona-selector {
    margin-bottom: 15px;
    padding: 10px;
    background-color: #f0f7ff;
    border-radius: 8px;
}
.drag-drop-area {
    border: 2px dashed #3498db;
    border-radius: 8px;
    padding: 25px;
    text-align: center;
    margin: 10px 0;
    background-color: #f0f7ff;
    transition: all 0.3s ease;
    cursor: pointer;
}
.drag-drop-area:hover {
    border-color: #2980b9;
    background-color: #e1f0fa;
    box-shadow: 0 0 10px rgba(52, 152, 219, 0.3);
}
/* Character card styling */
.character-card {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
    background-color: #f9f9f9;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s, box-shadow 0.3s;
    cursor: pointer;
}
.character-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}
.character-card img {
    transition: transform 0.3s;
    border-radius: 8px;
}
.character-card:hover img {
    transform: scale(1.05);
}
.character-card-buttons {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
}
/* Mobile UI improvements */
@media (max-width: 768px) {
    .chat-message {
        padding: 0.75rem;
        margin-bottom: 0.75rem;
    }
    .user-message {
        margin-left: 0.5rem;
    }
    .character-message {
        margin-right: 0.5rem;
    }
    .message-avatar {
        width: 32px;
        height: 32px;
    }
    .stButton > button {
        padding: 0.5rem;
        font-size: 0.9rem;
    }
    /* Improve form elements on mobile */
    input, select, textarea {
        font-size: 16px !important; /* Prevents zoom on focus in iOS */
    }
    /* Make sidebar full width on mobile when expanded */
    .st-emotion-cache-1cypcdb.ea3mdgi1 {
        width: 100% !important;
    }
    /* Improve mobile character cards */
    .character-card {
        margin-bottom: 15px;
    }
}
/* JSON import/export buttons */
.json-buttons {
    display: flex;
    gap: 10px;
    margin: 10px 0;
}
.json-buttons button {
    flex: 1;
    padding: 8px;
    border-radius: 5px;
    background-color: #f0f7ff;
    border: 1px solid #3498db;
    cursor: pointer;
    transition: all 0.2s ease;
}
.json-buttons button:hover {
    background-color: #e1f0fa;
}
</style>

<script>
function handleCardClick(characterName) {
    // Find the chat button for this character and click it
    const chatButton = document.querySelector(`button[key="chat_${characterName}"]`);
    if (chatButton) {
        chatButton.click();
    }
}
</script>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_character' not in st.session_state:
        st.session_state.current_character = None
    if 'current_persona' not in st.session_state:
        st.session_state.current_persona = None
    if 'editing_character' not in st.session_state:
        st.session_state.editing_character = False
    if 'editing_persona' not in st.session_state:
        st.session_state.editing_persona = False
    if 'api_key' not in st.session_state:
        # Try to load API key from environment variables
        api_key_from_env = os.environ.get("OPENROUTER_API_KEY", "")
        st.session_state.api_key = api_key_from_env
    if 'qwen_api_key' not in st.session_state:
        # Try to load Qwen API key from environment variables
        qwen_api_key_from_env = os.environ.get("QWEN_API_KEY", "")
        st.session_state.qwen_api_key = qwen_api_key_from_env
    if 'mistral_api_key' not in st.session_state:
        # Try to load Mistral API key from environment variables
        mistral_api_key_from_env = os.environ.get("MISTRAL_API_KEY", "")
        st.session_state.mistral_api_key = mistral_api_key_from_env
    if 'kimi_api_key' not in st.session_state:
        # Try to load Kimi API key from environment variables
        kimi_api_key_from_env = os.environ.get("KIMI_API_KEY", "")
        st.session_state.kimi_api_key = kimi_api_key_from_env
    if 'glm_api_key' not in st.session_state:
        # Try to load GLM API key from environment variables
        glm_api_key_from_env = os.environ.get("GLM_API_KEY", "")
        st.session_state.glm_api_key = glm_api_key_from_env
    if 'dolphin_api_key' not in st.session_state:
        # Try to load Dolphin API key from environment variables
        dolphin_api_key_from_env = os.environ.get("DOLPHIN_API_KEY", "")
        st.session_state.dolphin_api_key = dolphin_api_key_from_env
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "deepseek/deepseek-chat"
    # New session state variables for character card UI
    if 'chat_mode' not in st.session_state:
        st.session_state.chat_mode = False
    if 'editing_character_name' not in st.session_state:
        st.session_state.editing_character_name = None

def display_character_info(character):
    """Display character information in a nice format"""
    if character:
        # Create columns for avatar and info
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Display avatar if available
            if character.get('avatar_url'):
                try:
                    avatar_path = character['avatar_url']
                    if os.path.exists(avatar_path):
                        st.image(avatar_path, width=150)
                    elif avatar_path.startswith(('http://', 'https://')):
                        st.image(avatar_path, width=150)
                    else:
                        st.image("https://i.imgur.com/J5oMdG7.png", width=150)  # Default avatar
                except Exception as e:
                    st.image("https://i.imgur.com/J5oMdG7.png", width=150)  # Default avatar
                    st.error(f"Error loading avatar: {str(e)}")
            else:
                st.image("https://i.imgur.com/J5oMdG7.png", width=150)  # Default avatar
        
        with col2:
            st.markdown(f"""
            <div class="character-info">
                <h3>🎭 {character['name']}</h3>
                <p><strong>Personality:</strong> {character['personality']}</p>
                <p><strong>Backstory:</strong> {character['backstory']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display character memories if available
            if character.get('memories') and len(character['memories']) > 0:
                with st.expander("Character Memories", expanded=False):
                    for i, memory in enumerate(character['memories']):
                        col1, col2 = st.columns([0.8, 0.2])
                        with col1:
                            st.markdown(f"<div class='memory-item'>{memory}</div>", unsafe_allow_html=True)
                        with col2:
                            if st.button("🗑️", key=f"delete_memory_{i}"):
                                char_manager = CharacterManager()
                                char_manager.remove_memory_from_character(
                                    character['name'], i
                                )
                                # Refresh the current character
                                st.session_state.current_character = char_manager.get_character(
                                    character['name']
                                )
                                st.rerun()

def display_chat_message(message, is_user=True):
    """Display a chat message with proper styling"""
    # Process message to convert *emphasized text* to <em> tags
    import re
    processed_message = message
    if not is_user:  # Only process AI messages
        # Replace text between asterisks with <em> tags
        processed_message = re.sub(r'\*(.*?)\*', r'<em>\1</em>', message)
    
    if is_user:
        # Get user avatar if a persona is selected
        avatar_html = ""
        if st.session_state.current_persona and st.session_state.current_persona.get('avatar_url'):
            try:
                avatar_path = st.session_state.current_persona.get('avatar_url')
                # Check if it's a local file path or URL
                if os.path.exists(avatar_path):
                    # For local files, use the file:// protocol with absolute path
                    abs_path = os.path.abspath(avatar_path)
                    avatar_html = f'<img src="file://{abs_path}" class="message-avatar" alt="You" />'
                elif avatar_path and avatar_path.startswith(('http://', 'https://')):
                    # For URLs, use them directly
                    avatar_html = f'<img src="{avatar_path}" class="message-avatar" alt="You" />'
                else:
                    avatar_html = '<img src="https://i.imgur.com/J5oMdG7.png" class="message-avatar" alt="You" />'
            except Exception as e:
                print(f"Error loading persona avatar: {str(e)}")
                avatar_html = '<img src="https://i.imgur.com/J5oMdG7.png" class="message-avatar" alt="You" />'
        else:
            avatar_html = '<img src="https://i.imgur.com/J5oMdG7.png" class="message-avatar" alt="You" />'
            
        persona_name = st.session_state.current_persona.get('name', 'You') if st.session_state.current_persona else 'You'
        
        st.markdown(f"""
        <div class="chat-message user-message">
            {avatar_html}
            <div>
                <strong>{persona_name}:</strong><br>
                <span>{processed_message}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        character_name = st.session_state.current_character['name'] if st.session_state.current_character else "AI"
        
        # Get character avatar if available
        avatar_html = ""
        if not is_user and st.session_state.current_character and st.session_state.current_character.get('avatar_url'):
            try:
                avatar_path = st.session_state.current_character['avatar_url']
                # Check if it's a local file path or URL
                if os.path.exists(avatar_path):
                    # For local files, use the file:// protocol with absolute path
                    abs_path = os.path.abspath(avatar_path)
                    avatar_html = f'<img src="file://{abs_path}" class="message-avatar" alt="{character_name}" />'
                elif avatar_path.startswith(('http://', 'https://')):
                    # For URLs, use them directly
                    avatar_html = f'<img src="{avatar_path}" class="message-avatar" alt="{character_name}" />'
                else:
                    avatar_html = '<img src="https://i.imgur.com/J5oMdG7.png" class="message-avatar" alt="AI" />'
            except Exception as e:
                print(f"Error loading character avatar: {str(e)}")
                avatar_html = '<img src="https://i.imgur.com/J5oMdG7.png" class="message-avatar" alt="AI" />'
        else:
            # Default avatar
            avatar_html = '<img src="https://i.imgur.com/J5oMdG7.png" class="message-avatar" alt="AI" />'
        
        st.markdown(f"""
        <div class="chat-message character-message">
            {avatar_html}
            <div>
                <strong>{character_name}:</strong><br>
                <span>{processed_message}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def validate_api_key(api_key):
    """Validate the API key by making a test request"""
    if not api_key:
        return False
    
    try:
        api_handler = OpenRouterAPI(api_key)
        return api_handler.validate_api_key()
    except Exception as e:
        st.error(f"Error validating API key: {str(e)}")
        return False

def add_memory_to_character(character_name, memory_text):
    """Add a memory to a character"""
    if not memory_text.strip():
        return False
        
    char_manager = CharacterManager()
    result = char_manager.add_memory_to_character(character_name, memory_text.strip())
    if result:
        # Refresh the current character
        st.session_state.current_character = char_manager.get_character(character_name)
    return result

# Initialize session state variables at module level to ensure they exist before any function calls
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_character' not in st.session_state:
    st.session_state.current_character = None
if 'current_persona' not in st.session_state:
    st.session_state.current_persona = None
if 'editing_character' not in st.session_state:
    st.session_state.editing_character = False
if 'editing_persona' not in st.session_state:
    st.session_state.editing_persona = False
if 'api_key' not in st.session_state:
    # Try to load API key from environment variables
    api_key_from_env = os.environ.get("OPENROUTER_API_KEY", "")
    st.session_state.api_key = api_key_from_env
if 'qwen_api_key' not in st.session_state:
    # Try to load Qwen API key from environment variables
    qwen_api_key_from_env = os.environ.get("QWEN_API_KEY", "")
    st.session_state.qwen_api_key = qwen_api_key_from_env
if 'mistral_api_key' not in st.session_state:
    # Try to load Mistral API key from environment variables
    mistral_api_key_from_env = os.environ.get("MISTRAL_API_KEY", "")
    st.session_state.mistral_api_key = mistral_api_key_from_env
if 'kimi_api_key' not in st.session_state:
    # Try to load Kimi API key from environment variables
    kimi_api_key_from_env = os.environ.get("KIMI_API_KEY", "")
    st.session_state.kimi_api_key = kimi_api_key_from_env
if 'glm_api_key' not in st.session_state:
    # Try to load GLM API key from environment variables
    glm_api_key_from_env = os.environ.get("GLM_API_KEY", "")
    st.session_state.glm_api_key = glm_api_key_from_env
if 'dolphin_api_key' not in st.session_state:
    # Try to load Dolphin API key from environment variables
    dolphin_api_key_from_env = os.environ.get("DOLPHIN_API_KEY", "")
    st.session_state.dolphin_api_key = dolphin_api_key_from_env
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "deepseek/deepseek-chat"

def main():
    """Main application function"""
    # Call the initialize function for any additional setup
    initialize_session_state()
    
    # Initialize managers
    char_manager = CharacterManager()
    
    # Initialize chat mode if not present
    if 'chat_mode' not in st.session_state:
        st.session_state.chat_mode = False
    
    # Initialize selected character for editing
    if 'editing_character_name' not in st.session_state:
        st.session_state.editing_character_name = None
    
    # Initialize brief description field for characters
    if 'brief_description' not in st.session_state:
        st.session_state.brief_description = ""
    
    # Main title only shown in home mode
    if not st.session_state.chat_mode:
        st.title("🤖 AI Character Chat Interface")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        st.subheader("API Keys")
        api_key = st.text_input(
            "OpenRouter API Key (DeepSeek)", 
            type="password", 
            value=st.session_state.api_key,
            help="Enter your OpenRouter.ai API key for DeepSeek model"
        )
        if api_key:
            st.session_state.api_key = api_key
            
        qwen_api_key = st.text_input(
            "OpenRouter API Key (Qwen)", 
            type="password", 
            value=st.session_state.qwen_api_key,
            help="Enter your OpenRouter.ai API key for Qwen model"
        )
        if qwen_api_key:
            st.session_state.qwen_api_key = qwen_api_key
            
        mistral_api_key = st.text_input(
            "OpenRouter API Key (Mistral)", 
            type="password", 
            value=st.session_state.mistral_api_key,
            help="Enter your OpenRouter.ai API key for Mistral model"
        )
        if mistral_api_key:
            st.session_state.mistral_api_key = mistral_api_key
            
        kimi_api_key = st.text_input(
            "OpenRouter API Key (Kimi Dev 72B)", 
            type="password", 
            value=st.session_state.kimi_api_key,
            help="Enter your OpenRouter.ai API key for Kimi Dev 72B model"
        )
        if kimi_api_key:
            st.session_state.kimi_api_key = kimi_api_key
            
        glm_api_key = st.text_input(
            "OpenRouter API Key (THUDM GLM Z1 32B)", 
            type="password", 
            value=st.session_state.glm_api_key,
            help="Enter your OpenRouter.ai API key for THUDM GLM Z1 32B model"
        )
        if glm_api_key:
            st.session_state.glm_api_key = glm_api_key
            
        dolphin_api_key = st.text_input(
            "OpenRouter API Key (Dolphin 3.0)", 
            type="password", 
            value=st.session_state.dolphin_api_key,
            help="Enter your OpenRouter.ai API key for Dolphin 3.0 model"
        )
        if dolphin_api_key:
            st.session_state.dolphin_api_key = dolphin_api_key
            
        # Validate API keys
        if st.session_state.api_key:
            if 'api_key_valid' not in st.session_state or st.session_state.api_key_valid is None:
                with st.spinner("Validating DeepSeek API key..."):
                    is_valid = validate_api_key(st.session_state.api_key)
                    st.session_state.api_key_valid = is_valid
            
            if st.session_state.api_key_valid:
                st.success("✅ DeepSeek API key is valid")
            else:
                st.error("❌ DeepSeek API key is invalid or could not be validated")
        else:
            st.warning("Please enter your OpenRouter API key for DeepSeek")
            
        if st.session_state.qwen_api_key:
            if 'qwen_api_key_valid' not in st.session_state or st.session_state.qwen_api_key_valid is None:
                with st.spinner("Validating Qwen API key..."):
                    is_valid = validate_api_key(st.session_state.qwen_api_key)
                    st.session_state.qwen_api_key_valid = is_valid
            
            if st.session_state.qwen_api_key_valid:
                st.success("✅ Qwen API key is valid")
            else:
                st.error("❌ Qwen API key is invalid or could not be validated")
        else:
            st.warning("Please enter your OpenRouter API key for Qwen")
            
        if st.session_state.mistral_api_key:
            if 'mistral_api_key_valid' not in st.session_state or st.session_state.mistral_api_key_valid is None:
                with st.spinner("Validating Mistral API key..."):
                    is_valid = validate_api_key(st.session_state.mistral_api_key)
                    st.session_state.mistral_api_key_valid = is_valid
            
            if st.session_state.mistral_api_key_valid:
                st.success("✅ Mistral API key is valid")
            else:
                st.error("❌ Mistral API key is invalid or could not be validated")
        else:
            st.warning("Please enter your OpenRouter API key for Mistral")
            
        if st.session_state.kimi_api_key:
            if 'kimi_api_key_valid' not in st.session_state or st.session_state.kimi_api_key_valid is None:
                with st.spinner("Validating Kimi API key..."):
                    is_valid = validate_api_key(st.session_state.kimi_api_key)
                    st.session_state.kimi_api_key_valid = is_valid
            
            if st.session_state.kimi_api_key_valid:
                st.success("✅ Kimi API key is valid")
            else:
                st.error("❌ Kimi API key is invalid or could not be validated")
        else:
            st.warning("Please enter your OpenRouter API key for Kimi Dev 72B")
            
        if st.session_state.glm_api_key:
            if 'glm_api_key_valid' not in st.session_state or st.session_state.glm_api_key_valid is None:
                with st.spinner("Validating GLM API key..."):
                    is_valid = validate_api_key(st.session_state.glm_api_key)
                    st.session_state.glm_api_key_valid = is_valid
            
            if st.session_state.glm_api_key_valid:
                st.success("✅ GLM API key is valid")
            else:
                st.error("❌ GLM API key is invalid or could not be validated")
        else:
            st.warning("Please enter your OpenRouter API key for THUDM GLM Z1 32B")
            
        if st.session_state.dolphin_api_key:
            if 'dolphin_api_key_valid' not in st.session_state or st.session_state.dolphin_api_key_valid is None:
                with st.spinner("Validating Dolphin API key..."):
                    is_valid = validate_api_key(st.session_state.dolphin_api_key)
                    st.session_state.dolphin_api_key_valid = is_valid
            
            if st.session_state.dolphin_api_key_valid:
                st.success("✅ Dolphin API key is valid")
            else:
                st.error("❌ Dolphin API key is invalid or could not be validated")
        else:
            st.warning("Please enter your OpenRouter API key for Dolphin 3.0")
            
        # Add buttons for API key management
        st.subheader("API Key Management")
        
        # DeepSeek API key management
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.api_key and st.button("🔒 Clear DeepSeek Key"):
                st.session_state.api_key = ""
                st.session_state.api_key_valid = None
                st.rerun()
                
        # Qwen API key management
        col3, col4 = st.columns(2)
        with col3:
            if st.session_state.qwen_api_key and st.button("🔒 Clear Qwen Key"):
                st.session_state.qwen_api_key = ""
                st.session_state.qwen_api_key_valid = None
                st.rerun()
                
        # Mistral API key management
        col5, col6 = st.columns(2)
        with col5:
            if st.session_state.mistral_api_key and st.button("🔒 Clear Mistral Key"):
                st.session_state.mistral_api_key = ""
                st.session_state.mistral_api_key_valid = None
                st.rerun()
                
        # Kimi API key management
        col7, col8 = st.columns(2)
        with col7:
            if st.session_state.kimi_api_key and st.button("🔒 Clear Kimi Key"):
                st.session_state.kimi_api_key = ""
                st.session_state.kimi_api_key_valid = None
                st.rerun()
                
        # GLM API key management
        col9, col10 = st.columns(2)
        with col9:
            if st.session_state.glm_api_key and st.button("🔒 Clear GLM Key"):
                st.session_state.glm_api_key = ""
                st.session_state.glm_api_key_valid = None
                st.rerun()
                
        # Dolphin API key management
        col11, col12 = st.columns(2)
        with col11:
            if st.session_state.dolphin_api_key and st.button("🔒 Clear Dolphin Key"):
                st.session_state.dolphin_api_key = ""
                st.session_state.dolphin_api_key_valid = None
                st.rerun()
                
        with col2:
            if st.session_state.api_key and st.button("🔄 Test DeepSeek Connection"):
                with st.spinner("Testing connection to DeepSeek model..."):
                    api_handler = OpenRouterAPI(st.session_state.api_key)
                    result = api_handler.test_connection()
                    
                    if result["success"]:
                        st.success("✅ DeepSeek connection successful!")
                        with st.expander("View test details"):
                            st.write("**Response:**")
                            st.write(result["response"])
                            
                            st.write("**Token Usage:**")
                            st.text(f"Prompt Tokens: {result['usage']['prompt_tokens']}")
                            st.text(f"Completion Tokens: {result['usage']['completion_tokens']}")
                            st.text(f"Total Tokens: {result['usage']['total_tokens']}")
                            
                            st.write("**Cost Estimate:**")
                            st.text(f"${result['estimated_cost']:.6f}")
                    else:
                        st.error(f"❌ DeepSeek connection failed: {result['message']}")
                        
        with col4:
            if st.session_state.qwen_api_key and st.button("🔄 Test Qwen Connection"):
                with st.spinner("Testing connection to Qwen model..."):
                    api_handler = OpenRouterAPI(st.session_state.qwen_api_key)
                    result = api_handler.test_connection(model="qwen/qwen3-235b-a22b:free")
                    
                    if result["success"]:
                        st.success("✅ Qwen connection successful!")
                        with st.expander("View test details"):
                            st.write("**Response:**")
                            st.write(result["response"])
                            
                            st.write("**Token Usage:**")
                            st.text(f"Prompt Tokens: {result['usage']['prompt_tokens']}")
                            st.text(f"Completion Tokens: {result['usage']['completion_tokens']}")
                            st.text(f"Total Tokens: {result['usage']['total_tokens']}")
                            
                            st.write("**Cost Estimate:**")
                            st.text(f"${result['estimated_cost']:.6f}")
                    else:
                        st.error(f"❌ Qwen connection failed: {result['message']}")
                        
        with col6:
            if st.session_state.mistral_api_key and st.button("🔄 Test Mistral Connection"):
                with st.spinner("Testing connection to Mistral model..."):
                    api_handler = OpenRouterAPI(st.session_state.mistral_api_key)
                    result = api_handler.test_connection(model="mistralai/mistral-7b-instruct")
                    
                    if result["success"]:
                        st.success("✅ Mistral connection successful!")
                        with st.expander("View test details"):
                            st.write("**Response:**")
                            st.write(result["response"])
                            
                            st.write("**Token Usage:**")
                            st.text(f"Prompt Tokens: {result['usage']['prompt_tokens']}")
                            st.text(f"Completion Tokens: {result['usage']['completion_tokens']}")
                            st.text(f"Total Tokens: {result['usage']['total_tokens']}")
                            
                            st.write("**Cost Estimate:**")
                            st.text(f"${result['estimated_cost']:.6f}")
                    else:
                        st.error(f"❌ Mistral connection failed: {result['message']}")
                        
        with col8:
            if st.session_state.kimi_api_key and st.button("🔄 Test Kimi Connection"):
                with st.spinner("Testing connection to Kimi model..."):
                    api_handler = OpenRouterAPI(st.session_state.kimi_api_key)
                    result = api_handler.test_connection(model="01-ai/yi-large")
                    
                    if result["success"]:
                        st.success("✅ Kimi connection successful!")
                        with st.expander("View test details"):
                            st.write("**Response:**")
                            st.write(result["response"])
                            
                            st.write("**Token Usage:**")
                            st.text(f"Prompt Tokens: {result['usage']['prompt_tokens']}")
                            st.text(f"Completion Tokens: {result['usage']['completion_tokens']}")
                            st.text(f"Total Tokens: {result['usage']['total_tokens']}")
                            
                            st.write("**Cost Estimate:**")
                            st.text(f"${result['estimated_cost']:.6f}")
                    else:
                        st.error(f"❌ Kimi connection failed: {result['message']}")
                        
        with col10:
            if st.session_state.glm_api_key and st.button("🔄 Test GLM Connection"):
                with st.spinner("Testing connection to GLM model..."):
                    api_handler = OpenRouterAPI(st.session_state.glm_api_key)
                    result = api_handler.test_connection(model="thudm/glm-z1-32b:free")
                    
                    if result["success"]:
                        st.success("✅ GLM connection successful!")
                        with st.expander("View test details"):
                            st.write("**Response:**")
                            st.write(result["response"])
                            
                            st.write("**Token Usage:**")
                            st.text(f"Prompt Tokens: {result['usage']['prompt_tokens']}")
                            st.text(f"Completion Tokens: {result['usage']['completion_tokens']}")
                            st.text(f"Total Tokens: {result['usage']['total_tokens']}")
                            
                            st.write("**Cost Estimate:**")
                            st.text(f"${result['estimated_cost']:.6f}")
                    else:
                        st.error(f"❌ GLM connection failed: {result['message']}")
                        
        with col12:
            if st.session_state.dolphin_api_key and st.button("🔄 Test Dolphin Connection"):
                with st.spinner("Testing connection to Dolphin model..."):
                    api_handler = OpenRouterAPI(st.session_state.dolphin_api_key)
                    result = api_handler.test_connection(model="cognitivecomputations/dolphin3.0-mistral-24b:free")
                    
                    if result["success"]:
                        st.success("✅ Dolphin connection successful!")
                        with st.expander("View test details"):
                            st.write("**Response:**")
                            st.write(result["response"])
                            
                            st.write("**Token Usage:**")
                            st.text(f"Prompt Tokens: {result['usage']['prompt_tokens']}")
                            st.text(f"Completion Tokens: {result['usage']['completion_tokens']}")
                            st.text(f"Total Tokens: {result['usage']['total_tokens']}")
                            
                            st.write("**Cost Estimate:**")
                            st.text(f"${result['estimated_cost']:.6f}")
                    else:
                        st.error(f"❌ Dolphin connection failed: {result['message']}")

        
        # Model selection with pricing info
        models = [
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat", "cost": "$0.50 / 1M tokens"},
            {"id": "qwen/qwen3-235b-a22b:free", "name": "Qwen", "cost": "$0.50 / 1M tokens"},
            {"id": "openai/gpt-4o", "name": "GPT-4o", "cost": "$5.00 / 1M tokens"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "cost": "$0.80 / 1M tokens"},
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "cost": "$3.00 / 1M tokens"},
            {"id": "mistralai/mistral-7b-instruct", "name": "Mistral 7B", "cost": "$0.20 / 1M tokens"},
            {"id": "meta-llama/llama-3.1-8b-instruct", "name": "Llama 3.1 8B", "cost": "$0.20 / 1M tokens"},
            {"id": "01-ai/yi-large", "name": "Kimi Dev 72B", "cost": "$1.50 / 1M tokens"},
            {"id": "thudm/glm-z1-32b:free", "name": "THUDM: GLM Z1 32B", "cost": "$1.00 / 1M tokens"},
            {"id": "cognitivecomputations/dolphin3.0-mistral-24b:free", "name": "Dolphin 3.0", "cost": "$0.20 / 1M tokens"}
        ]
        
        model_ids = [model["id"] for model in models]
        model_names = [f"{model['name']} ({model['cost']})" for model in models]
        
        selected_index = model_ids.index(st.session_state.selected_model) if st.session_state.selected_model in model_ids else 0
        
        selected_model_name = st.selectbox(
            "Select Model",
            model_names,
            index=selected_index
        )
        
        selected_model = model_ids[model_names.index(selected_model_name)]
        st.session_state.selected_model = selected_model
        
        # Display model info
        selected_model_info = next((model for model in models if model["id"] == selected_model), None)
        if selected_model_info:
            st.info(f"Using {selected_model_info['name']} (Approx. cost: {selected_model_info['cost']})")
            
            # Show model-specific messages
            if "deepseek" in selected_model.lower():
                st.success("✅ Using DeepSeek model as requested")
            elif "qwen" in selected_model.lower():
                st.success("✅ Using Qwen model as requested")
            elif "mistral" in selected_model.lower():
                st.success("✅ Using Mistral model as requested")
            elif "yi-large" in selected_model.lower():
                st.success("✅ Using Kimi Dev 72B model as requested")
            elif "glm" in selected_model.lower():
                st.success("✅ Using THUDM GLM Z1 32B model as requested")
            elif "dolphin" in selected_model.lower():
                st.success("✅ Using Dolphin 3.0 model as requested")

        
        # Model parameters
        st.subheader("Model Parameters")
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        max_tokens = st.slider("Max Tokens", 100, 4000, 1000, 100)
        
        st.divider()
        
        # User Persona Management
        st.header("👤 User Persona Management")
        
        # Load available personas
        personas = char_manager.load_personas()
        persona_names = ["None"] + [persona["name"] for persona in personas]
        
        # Persona selection
        selected_persona_name = st.selectbox(
            "Choose your persona",
            persona_names
        )
        
        if selected_persona_name != "None":
            selected_persona = next((persona for persona in personas if persona['name'] == selected_persona_name), None)
            if selected_persona != st.session_state.current_persona:
                st.session_state.current_persona = selected_persona
        else:
            st.session_state.current_persona = None
            
        # Persona management
        with st.expander("Manage User Personas"):
            persona_action = st.radio("Action", ["Create New Persona", "Edit Current Persona", "Delete Current Persona"])
            
            if persona_action == "Create New Persona" or (persona_action == "Edit Current Persona" and st.session_state.current_persona):
                with st.form(key="persona_form"):
                    if persona_action == "Create New Persona":
                        persona_name = st.text_input("Name")
                    else:
                        persona_name = st.text_input("Name", value=st.session_state.current_persona.get("name"), disabled=True)
                        st.info("Name cannot be changed once created")
                    
                    persona_age = st.number_input("Age", min_value=1, max_value=120, 
                                                value=st.session_state.current_persona.get("age", 25) if persona_action == "Edit Current Persona" else 25)
                    persona_background = st.text_area("Background", 
                                                    value=st.session_state.current_persona.get("background", "") if persona_action == "Edit Current Persona" else "")
                    persona_backstory = st.text_area("Backstory", 
                                                   value=st.session_state.current_persona.get("backstory", "") if persona_action == "Edit Current Persona" else "")
                    persona_additional_info = st.text_area("Additional Information", 
                                                         value=st.session_state.current_persona.get("additional_info", "") if persona_action == "Edit Current Persona" else "")
                    
                    # Avatar options
                    avatar_option = st.radio("Avatar Option", ["Default", "URL", "Upload Image"])
                    
                    if avatar_option == "Default":
                        avatar_url = "https://i.imgur.com/J5oMdG7.png"  # Default avatar
                    elif avatar_option == "URL":
                        avatar_url = st.text_input("Avatar URL", 
                                                 value=st.session_state.current_persona.get("avatar_url", "") if persona_action == "Edit Current Persona" else "")
                    else:  # Upload Image
                        st.info("Click below to open your file manager. Only JPEG, JPG, or PNG files are accepted.")
                        uploaded_file = st.file_uploader("Upload Avatar Image", type=["jpg", "jpeg", "png"], key="persona_avatar", accept_multiple_files=False)
                        avatar_url = st.session_state.current_persona.get("avatar_url", "") if persona_action == "Edit Current Persona" else ""
                        
                        # Add drag and drop area with better instructions
                        st.markdown("""
                        <div class="drag-drop-area">
                            <p>📁 Click above to browse files or drag and drop your image here</p>
                            <p style="font-size: 0.8em; color: #666;">Supported formats: JPEG, JPG, PNG</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if uploaded_file is not None:
                            # Create directory if it doesn't exist
                            os.makedirs("uploaded_images/personas", exist_ok=True)
                            
                            # Save the uploaded file
                            file_path = os.path.join("uploaded_images/personas", uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            avatar_url = file_path
                    
                    submit_button = st.form_submit_button("Save Persona")
                    
                    if submit_button:
                        if persona_action == "Create New Persona" and not persona_name:
                            st.error("Please provide a name for the persona")
                        else:
                            # Create or update persona
                            new_persona = {
                                "name": persona_name,
                                "age": persona_age,
                                "background": persona_background,
                                "backstory": persona_backstory,
                                "additional_info": persona_additional_info,
                                "avatar_url": avatar_url,
                                "created_at": datetime.now().isoformat() if persona_action == "Create New Persona" else st.session_state.current_persona.get("created_at")
                            }
                            
                            char_manager.save_persona(new_persona)
                            st.session_state.current_persona = new_persona
                            st.success(f"Persona {persona_name} {'created' if persona_action == 'Create New Persona' else 'updated'}!")
                            st.rerun()
            
            elif persona_action == "Delete Current Persona" and st.session_state.current_persona:
                st.warning(f"Are you sure you want to delete the persona '{st.session_state.current_persona.get('name')}'?")
                if st.button("Confirm Delete"):
                    if char_manager.delete_persona(st.session_state.current_persona.get("name")):
                        st.session_state.current_persona = None
                        st.success("Persona deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete persona")
        
        st.divider()
        
        # Character management - Create option only in sidebar
        st.header("👥 Create Character")

        # Load existing characters (but don't show selection in sidebar)
        characters = char_manager.load_characters()
        
        # Character management options
        with st.expander("Manage Characters"):
            character_action = st.radio("Action", ["Create New Character", "Edit Current Character", "Delete Current Character"])
            
            if character_action == "Create New Character" or (character_action == "Edit Current Character" and st.session_state.current_character):
                with st.form("character_form"):
                    if character_action == "Create New Character":
                        char_name = st.text_input("Character Name")
                    else:
                        char_name = st.text_input("Character Name", value=st.session_state.current_character.get("name"), disabled=True)
                        st.info("Name cannot be changed once created")
                    
                    char_personality = st.text_area("Personality Traits", height=100,
                                                  value=st.session_state.current_character.get("personality", "") if character_action == "Edit Current Character" else "")
                    char_backstory = st.text_area("Backstory", height=100,
                                                value=st.session_state.current_character.get("backstory", "") if character_action == "Edit Current Character" else "")
                    
                    # Avatar options
                    avatar_option = st.radio("Avatar Option", ["Default", "URL", "Upload Image"])
                    
                    if avatar_option == "Default":
                        # Show default avatars from default_images directory
                        if os.path.exists("default_images"):
                            default_avatars = [f for f in os.listdir("default_images") if f.endswith((".jpg", ".jpeg", ".png"))]
                            if default_avatars:
                                selected_default = st.selectbox("Choose a default avatar", default_avatars)
                                char_avatar = os.path.join("default_images", selected_default)
                            else:
                                st.warning("No default avatars found")
                                char_avatar = ""
                        else:
                            st.warning("Default images directory not found")
                            char_avatar = ""
                    elif avatar_option == "URL":
                        char_avatar = st.text_input("Avatar URL",
                                                  value=st.session_state.current_character.get("avatar_url", "") if character_action == "Edit Current Character" else "")
                    else:  # Upload Image
                        st.info("Click below to open your file manager. Only JPEG, JPG, or PNG files are accepted.")
                        uploaded_file = st.file_uploader("Upload Character Image", type=["jpg", "jpeg", "png"], key="character_avatar", accept_multiple_files=False)
                        char_avatar = st.session_state.current_character.get("avatar_url", "") if character_action == "Edit Current Character" else ""
                        
                        # Add drag and drop area with better instructions
                        st.markdown("""
                        <div class="drag-drop-area">
                            <p>📁 Click above to browse files or drag and drop your image here</p>
                            <p style="font-size: 0.8em; color: #666;">Supported formats: JPEG, JPG, PNG</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if uploaded_file is not None:
                            # Create directory if it doesn't exist
                            os.makedirs("uploaded_images/characters", exist_ok=True)
                            
                            # Save the uploaded file
                            file_path = os.path.join("uploaded_images/characters", uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            char_avatar = file_path
                    
                    # Memory section (only for editing)
                    if character_action == "Edit Current Character" and st.session_state.current_character:
                        st.subheader("Character Memories")
                        memories = st.session_state.current_character.get("memories", [])
                        
                        for i, memory in enumerate(memories):
                            col1, col2 = st.columns([0.8, 0.2])
                            with col1:
                                st.markdown(f"<div class='memory-item'>{memory}</div>", unsafe_allow_html=True)
                            with col2:
                                if st.button("🗑️", key=f"delete_memory_form_{i}"):
                                    char_manager.remove_memory_from_character(
                                        st.session_state.current_character["name"], i
                                    )
                                    # Refresh the current character
                                    st.session_state.current_character = char_manager.get_character(
                                        st.session_state.current_character["name"]
                                    )
                                    st.rerun()
                        
                        new_memory = st.text_area("Add new memory", height=100, key="new_memory_form")
                    
                    if st.form_submit_button("Save Character"):
                        if character_action == "Create New Character":
                            if not char_name or not char_personality:
                                st.error("Please fill in at least name and personality.")
                            else:
                                new_character = {
                                    "name": char_name,
                                    "personality": char_personality,
                                    "backstory": char_backstory,
                                    "avatar_url": char_avatar,
                                    "memories": [],
                                    "created_at": datetime.now().isoformat()
                                }
                                char_manager.save_character(new_character)
                                st.session_state.current_character = new_character
                                st.success(f"Character '{char_name}' created successfully!")
                                st.rerun()
                        else:  # Edit Current Character
                            if not char_personality:
                                st.error("Personality cannot be empty.")
                            else:
                                # Update character
                                updated_data = {
                                    "personality": char_personality,
                                    "backstory": char_backstory,
                                    "avatar_url": char_avatar
                                }
                                
                                # Add new memory if provided
                                if "new_memory_form" in st.session_state and st.session_state.new_memory_form.strip():
                                    add_memory_to_character(st.session_state.current_character["name"], st.session_state.new_memory_form)
                                
                                char_manager.update_character(char_name, updated_data)
                                st.session_state.current_character = char_manager.get_character(char_name)
                                st.success(f"Character '{char_name}' updated successfully!")
                                st.rerun()
            
            elif character_action == "Delete Current Character" and st.session_state.current_character:
                st.warning(f"Are you sure you want to delete the character '{st.session_state.current_character.get('name')}'?")
                if st.button("Confirm Delete"):
                    if char_manager.delete_character(st.session_state.current_character.get("name")):
                        st.session_state.current_character = None
                        st.session_state.chat_history = []
                        st.success("Character deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete character")
        
        # Chat controls
        st.divider()
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
        
        if st.button("💾 Save Chat History"):
            if st.session_state.chat_history:
                char_manager.save_chat_history(st.session_state.chat_history, st.session_state.current_character)
                st.success("Chat history saved!")
    
    # Main content area - either character cards or chat interface
    if not st.session_state.chat_mode:
        # Display character cards in a grid
        st.header("👥 Your Characters")
        
        # Load all characters
        characters = char_manager.load_characters()
        
        # Function to handle character card click
        def character_card_clicked(character_name):
            selected_char = next((char for char in characters if char['name'] == character_name), None)
            if selected_char:
                st.session_state.current_character = selected_char
                st.session_state.chat_history = []  # Clear chat when switching characters
                st.session_state.chat_mode = True
                st.rerun()
        
        # Function to handle edit character button
        def edit_character_button_clicked(character_name):
            st.session_state.editing_character_name = character_name
            st.rerun()
        
        # Display character cards in a grid
        if characters:
            # Use columns to create a responsive grid
            cols = st.columns(3)  # 3 columns for desktop, will stack on mobile
            
            for i, character in enumerate(characters):
                with cols[i % 3]:
                    # Create a card-like container with border and padding using our CSS class
                    st.markdown(f"""
                    <div class='character-card' onclick='handleCardClick("{character['name']}");'>
                        <h3 style='text-align: center; color: #2980b9; margin-bottom: 10px;'>{character['name']}</h3>
                    """, unsafe_allow_html=True)
                    
                    # Display character avatar
                    if character.get('avatar_url'):
                        try:
                            avatar_path = character['avatar_url']
                            if os.path.exists(avatar_path):
                                st.image(avatar_path, width=150, use_column_width=True)
                            elif avatar_path.startswith(('http://', 'https://')):
                                st.image(avatar_path, width=150, use_column_width=True)
                            else:
                                st.image("https://i.imgur.com/J5oMdG7.png", width=150, use_column_width=True)
                        except Exception as e:
                            st.image("https://i.imgur.com/J5oMdG7.png", width=150, use_column_width=True)
                    else:
                        st.image("https://i.imgur.com/J5oMdG7.png", width=150, use_column_width=True)
                    
                    # Display brief description
                    brief_desc = character.get('brief_description', 'No description available')
                    st.markdown(f"<p style='text-align: center;'>{brief_desc}</p>", unsafe_allow_html=True)
                    
                    # Close the character card div
                    st.markdown("""</div>""", unsafe_allow_html=True)
                    
                    # Chat and Edit buttons in a separate div with our CSS class
                    st.markdown("""<div class='character-card-buttons'>""", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"💬 Chat", key=f"chat_{character['name']}"):
                            character_card_clicked(character['name'])
                    with col2:
                        if st.button(f"✏️ Edit", key=f"edit_{character['name']}"):
                            edit_character_button_clicked(character['name'])
                    st.markdown("""</div>""", unsafe_allow_html=True)
        else:
            st.info("No characters found. Create a new character using the sidebar.")
        
        # Character editing interface if a character is selected for editing
        if st.session_state.editing_character_name:
            edit_char = next((char for char in characters if char['name'] == st.session_state.editing_character_name), None)
            if edit_char:
                st.header(f"✏️ Edit {edit_char['name']}")
                
                with st.form("edit_character_form"):
                    # Character fields
                    brief_description = st.text_input("Brief Description", 
                                                   value=edit_char.get("brief_description", ""))
                    char_personality = st.text_area("Personality Traits", height=100,
                                                  value=edit_char.get("personality", ""))
                    char_backstory = st.text_area("Backstory", height=100,
                                                value=edit_char.get("backstory", ""))
                    
                    # Avatar options
                    avatar_option = st.radio("Avatar Option", ["Keep Current", "Default", "URL", "Upload Image"])
                    
                    char_avatar = edit_char.get("avatar_url", "")
                    
                    if avatar_option == "Default":
                        # Show default avatars from default_images directory
                        if os.path.exists("default_images"):
                            default_avatars = [f for f in os.listdir("default_images") if f.endswith((".jpg", ".jpeg", ".png"))]
                            if default_avatars:
                                selected_default = st.selectbox("Choose a default avatar", default_avatars)
                                char_avatar = os.path.join("default_images", selected_default)
                            else:
                                st.warning("No default avatars found")
                        else:
                            st.warning("Default images directory not found")
                    elif avatar_option == "URL":
                        char_avatar = st.text_input("Avatar URL", value="")
                    elif avatar_option == "Upload Image":
                        st.info("Click below to open your file manager. Only JPEG, JPG, or PNG files are accepted.")
                        uploaded_file = st.file_uploader("Upload Character Image", type=["jpg", "jpeg", "png"], key="edit_character_avatar", accept_multiple_files=False)
                        
                        # Add drag and drop area with better instructions
                        st.markdown("""
                        <div class="drag-drop-area">
                            <p>📁 Click above to browse files or drag and drop your image here</p>
                            <p style="font-size: 0.8em; color: #666;">Supported formats: JPEG, JPG, PNG</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if uploaded_file is not None:
                            # Create directory if it doesn't exist
                            os.makedirs("uploaded_images/characters", exist_ok=True)
                            
                            # Save the uploaded file
                            file_path = os.path.join("uploaded_images/characters", uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            char_avatar = file_path
                    
                    # Memory section
                    st.subheader("Character Memories")
                    memories = edit_char.get("memories", [])
                    
                    for i, memory in enumerate(memories):
                        col1, col2 = st.columns([0.8, 0.2])
                        with col1:
                            st.markdown(f"<div class='memory-item'>{memory}</div>", unsafe_allow_html=True)
                        with col2:
                            if st.button("🗑️", key=f"delete_memory_edit_{i}"):
                                char_manager.remove_memory_from_character(
                                    edit_char["name"], i
                                )
                                # Refresh the character
                                st.session_state.editing_character_name = None
                                st.rerun()
                    
                    new_memory = st.text_area("Add new memory", height=100, key="new_memory_edit")
                    
                    # Save and Cancel buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes"):
                            if not char_personality:
                                st.error("Personality cannot be empty.")
                            else:
                                # Update character
                                updated_data = {
                                    "brief_description": brief_description,
                                    "personality": char_personality,
                                    "backstory": char_backstory,
                                    "avatar_url": char_avatar
                                }
                                
                                # Add new memory if provided
                                if "new_memory_edit" in st.session_state and st.session_state.new_memory_edit.strip():
                                    add_memory_to_character(edit_char["name"], st.session_state.new_memory_edit)
                                
                                char_manager.update_character(edit_char["name"], updated_data)
                                st.session_state.editing_character_name = None
                                st.success(f"Character '{edit_char['name']}' updated successfully!")
                                st.rerun()
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.editing_character_name = None
                            st.rerun()
    else:
        # Chat interface
        # Back button to return to character selection
        if st.button("← Back to Characters"):
            st.session_state.chat_mode = False
            st.rerun()
            
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("💬 Chat")
            
            # Display current character info
            if st.session_state.current_character:
                display_character_info(st.session_state.current_character)
            else:
                st.info("Please select or create a character to start chatting.")
            
            # Chat history display
            chat_container = st.container()
            with chat_container:
                for i, (user_msg, char_msg) in enumerate(st.session_state.chat_history):
                    display_chat_message(user_msg, is_user=True)
                    display_chat_message(char_msg, is_user=False)
            
            # Chat input
            # Check if we have the appropriate API key for the selected model
            has_required_api_key = False
            if "qwen" in st.session_state.selected_model.lower() and st.session_state.qwen_api_key:
                has_required_api_key = True
            elif "mistral" in st.session_state.selected_model.lower() and st.session_state.mistral_api_key:
                has_required_api_key = True
            elif "yi-large" in st.session_state.selected_model.lower() and st.session_state.kimi_api_key:
                has_required_api_key = True
            elif "glm" in st.session_state.selected_model.lower() and st.session_state.glm_api_key:
                has_required_api_key = True
            elif "dolphin" in st.session_state.selected_model.lower() and st.session_state.dolphin_api_key:
                has_required_api_key = True
            elif st.session_state.api_key:
                has_required_api_key = True
                
            if st.session_state.current_character:
                    
                if has_required_api_key:
                    user_input = st.text_area(
                        "Your message:",
                        height=100,
                        key="user_input",
                        placeholder="Type your message here..."
                    )
                else:
                    if "qwen" in st.session_state.selected_model.lower():
                        st.warning("Please enter your Qwen API key in the sidebar.")
                    elif "mistral" in st.session_state.selected_model.lower():
                        st.warning("Please enter your Mistral API key in the sidebar.")
                    elif "yi-large" in st.session_state.selected_model.lower():
                        st.warning("Please enter your Kimi API key in the sidebar.")
                    elif "glm" in st.session_state.selected_model.lower():
                        st.warning("Please enter your GLM API key in the sidebar.")
                    elif "dolphin" in st.session_state.selected_model.lower():
                        st.warning("Please enter your Dolphin API key in the sidebar.")
                    else:
                        st.warning("Please enter your OpenRouter API key in the sidebar.")
                
                col_send, col_clear = st.columns([3, 1])
                with col_send:
                    if st.button("📤 Send Message", type="primary"):
                        if user_input.strip():
                            # Initialize API handler with the appropriate API key based on the selected model
                            if "qwen" in st.session_state.selected_model.lower() and st.session_state.qwen_api_key:
                                api_handler = OpenRouterAPI(st.session_state.qwen_api_key)
                            elif "mistral" in st.session_state.selected_model.lower() and st.session_state.mistral_api_key:
                                api_handler = OpenRouterAPI(st.session_state.mistral_api_key)
                            elif "yi-large" in st.session_state.selected_model.lower() and st.session_state.kimi_api_key:
                                api_handler = OpenRouterAPI(st.session_state.kimi_api_key)
                            elif "glm" in st.session_state.selected_model.lower() and st.session_state.glm_api_key:
                                api_handler = OpenRouterAPI(st.session_state.glm_api_key)
                            elif "dolphin" in st.session_state.selected_model.lower() and st.session_state.dolphin_api_key:
                                api_handler = OpenRouterAPI(st.session_state.dolphin_api_key)
                            else:
                                api_handler = OpenRouterAPI(st.session_state.api_key)
                            
                            # Create system prompt from character and persona
                            system_prompt = char_manager.create_system_prompt(
                                st.session_state.current_character,
                                st.session_state.current_persona
                            )
                            
                            # Prepare messages for API
                            messages = [{"role": "system", "content": system_prompt}]
                            
                            # Add chat history
                            for user_msg, char_msg in st.session_state.chat_history[-5:]:  # Last 5 exchanges
                                messages.append({"role": "user", "content": user_msg})
                                messages.append({"role": "assistant", "content": char_msg})
                            
                            # Add current message
                            messages.append({"role": "user", "content": user_input})
                            
                            # Show loading spinner
                            with st.spinner("Thinking..."):
                                try:
                                    response_data = api_handler.get_response(
                                        messages=messages,
                                        model=st.session_state.selected_model,
                                        temperature=temperature,
                                        max_tokens=max_tokens
                                    )
                        
                                    if isinstance(response_data, dict) and "content" in response_data:
                                        # Add to chat history
                                        st.session_state.chat_history.append((user_input, response_data["content"]))
                                        
                                        # Store token usage data if available
                                        if "usage" in response_data:
                                            if "usage" not in st.session_state:
                                                st.session_state.usage = {
                                                    "prompt_tokens": 0,
                                                    "completion_tokens": 0,
                                                    "total_tokens": 0,
                                                    "estimated_cost": 0.0
                                                }
                                            
                                            # Update token usage stats
                                            st.session_state.usage["prompt_tokens"] += response_data["usage"].get("prompt_tokens", 0)
                                            st.session_state.usage["completion_tokens"] += response_data["usage"].get("completion_tokens", 0)
                                            st.session_state.usage["total_tokens"] += response_data["usage"].get("total_tokens", 0)
                                            st.session_state.usage["estimated_cost"] = response_data.get("estimated_cost", 0.0)
                                        
                                        st.rerun()
                                    else:
                                        st.error("Failed to get response from API")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            else:
                if not st.session_state.current_character:
                    st.warning("Please select a character first.")
                if not has_required_api_key:
                    if "qwen" in st.session_state.selected_model.lower():
                        st.warning("Please enter your Qwen API key in the sidebar.")
                    elif "mistral" in st.session_state.selected_model.lower():
                        st.warning("Please enter your Mistral API key in the sidebar.")
                    elif "yi-large" in st.session_state.selected_model.lower():
                        st.warning("Please enter your Kimi API key in the sidebar.")
                    elif "glm" in st.session_state.selected_model.lower():
                        st.warning("Please enter your GLM API key in the sidebar.")
                    elif "dolphin" in st.session_state.selected_model.lower():
                        st.warning("Please enter your Dolphin API key in the sidebar.")
                    else:
                        st.warning("Please enter your OpenRouter API key in the sidebar.")
        
        with col2:
            st.header("📊 Chat Stats")
            
            if st.session_state.chat_history:
                st.metric("Messages Exchanged", len(st.session_state.chat_history) * 2)
                
                # Word count
                total_words = sum(len(msg.split()) for user_msg, char_msg in st.session_state.chat_history for msg in [user_msg, char_msg])
                st.metric("Total Words", total_words)
                
                # Token Usage Stats
                if "usage" in st.session_state:
                    st.subheader("Token Usage")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.text(f"Prompt Tokens: {st.session_state.usage['prompt_tokens']:,}")
                        st.text(f"Completion Tokens: {st.session_state.usage['completion_tokens']:,}")
                    
                    with col2:
                        st.text(f"Total Tokens: {st.session_state.usage['total_tokens']:,}")
                        # Display estimated cost with formatting
                        cost = st.session_state.usage['estimated_cost']
                        st.text(f"Est. Cost: ${cost:.6f}")
                    
                    # Add a progress bar for visual representation
                    if cost > 0:
                        # Use a logarithmic scale for better visualization
                        # $0.01 is a reasonable threshold for showing progress
                        progress = min(cost / 0.01, 1.0)
                        st.progress(progress)
                        
                        if progress >= 1.0:
                            st.warning("⚠️ Cost threshold reached")
                            
                    # Add token usage display in the sidebar as well
                    st.sidebar.subheader("Token Usage")
                    st.sidebar.text(f"Total Tokens: {st.session_state.usage['total_tokens']:,}")
                    st.sidebar.text(f"Est. Cost: ${cost:.6f}")
                    
                    # Add a progress bar for visual representation in sidebar
                    if cost > 0:
                        # Use a logarithmic scale for better visualization
                        progress = min(cost / 0.01, 1.0)
                        st.sidebar.progress(progress)
            else:
                st.info("No chat history yet.")
        
        # Character list
        st.subheader("Available Characters")
        characters = char_manager.load_characters()
        for char in characters:
            with st.expander(f"🎭 {char['name']}"):
                st.write(f"**Personality:** {char['personality'][:100]}...")
                # Use a form to prevent page refresh issues
                with st.form(key=f"load_char_form_{char['name']}"):
                    if st.form_submit_button(f"Load {char['name']}"):
                        st.session_state.current_character = char
                        st.session_state.chat_history = []
                        st.rerun()
        
        # JSON Import/Export for Characters and Chat History
        st.subheader("Import/Export")
        
        # Export Character
        if st.session_state.current_character:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📤 Export Character"):
                    char_json = json.dumps(st.session_state.current_character, indent=2)
                    st.download_button(
                        label="Download Character JSON",
                        data=char_json,
                        file_name=f"{st.session_state.current_character['name']}.json",
                        mime="application/json"
                    )
            
            # Export Chat History
            with col2:
                if st.button("📤 Export Chat History") and st.session_state.chat_history:
                    chat_data = {
                        "character": st.session_state.current_character,
                        "timestamp": datetime.now().isoformat(),
                        "messages": []
                    }
                    
                    for user_msg, char_msg in st.session_state.chat_history:
                        chat_data["messages"].append({
                            "user": user_msg,
                            "character": char_msg
                        })
                    
                    chat_json = json.dumps(chat_data, indent=2)
                    st.download_button(
                        label="Download Chat History JSON",
                        data=chat_json,
                        file_name=f"{st.session_state.current_character['name']}_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        
        # Import Character
        with st.expander("Import Character or Chat History"):
            import_type = st.radio("Import Type", ["Character", "Chat History"])
            uploaded_file = st.file_uploader(f"Upload {import_type} JSON", type=["json"])
            
            if uploaded_file is not None:
                try:
                    content = uploaded_file.read()
                    data = json.loads(content)
                    
                    if import_type == "Character":
                        # Validate character data
                        if "name" in data and "personality" in data and "backstory" in data:
                            # Save character
                            char_manager.save_character(data)
                            st.success(f"Character '{data['name']}' imported successfully!")
                            
                            # Ask if user wants to load this character
                            if st.button(f"Load imported character: {data['name']}"):
                                st.session_state.current_character = data
                                st.session_state.chat_history = []
                                st.rerun()
                        else:
                            st.error("Invalid character data. JSON must include name, personality, and backstory.")
                    
                    elif import_type == "Chat History":
                        # Validate chat history data
                        if "character" in data and "messages" in data:
                            # Check if character exists
                            character = data.get("character")
                            if character and "name" in character:
                                # Convert messages to the format used by the app
                                chat_history = []
                                for msg in data.get("messages", []):
                                    chat_history.append((msg.get("user", ""), msg.get("character", "")))
                                
                                # Load the character and chat history
                                st.session_state.current_character = character
                                st.session_state.chat_history = chat_history
                                st.success(f"Chat history with '{character['name']}' imported successfully!")
                                st.rerun()
                            else:
                                st.error("Invalid chat history data. Character information is missing.")
                        else:
                            st.error("Invalid chat history data. JSON must include character and messages.")
                            
                except Exception as e:
                    st.error(f"Error importing file: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())

if __name__ == "__main__":
    main()