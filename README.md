# AI Character Chat Interface

A web-based AI character chat interface similar to Character.AI or CrushOn.AI, built with Python and Streamlit. This application allows users to create and chat with custom AI characters using various language models via the OpenRouter.ai API.

## Features

- Create custom characters with unique personalities, backstories, and avatars
- Chat with AI characters that maintain their defined personalities
- Choose from multiple language models (GPT-4, DeepSeek, Claude, etc.)
- Save and load chat histories
- Responsive UI with character information display
- Customizable model parameters (temperature, max tokens)

## Prerequisites

- Python 3.8 or higher
- OpenRouter.ai API key

## Installation

1. Clone this repository or download the files

2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Create a `.env` file in the project root directory with your API keys (optional but recommended):

```
# .env file example
OPENROUTER_API_KEY=your_openrouter_api_key_here
QWEN_API_KEY=your_qwen_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
KIMI_API_KEY=your_kimi_api_key_here
GLM_API_KEY=your_glm_api_key_here
DOLPHIN_API_KEY=your_dolphin_api_key_here
```

2. Run the Streamlit app:

```bash
streamlit run main.py
```

3. Open your web browser and go to `http://localhost:8501`

4. If you didn't set up the `.env` file, enter your OpenRouter.ai API key(s) in the sidebar

5. Select or create a character

6. Start chatting!

## Project Structure

- `main.py`: Main application file with Streamlit UI
- `character_utils.py`: Character management functionality
- `api_handler.py`: OpenRouter API integration
- `sample_characters.json`: Sample character profiles
- `characters/`: Directory where character profiles are stored
- `chat_history/`: Directory where chat histories are saved

## Creating Characters

To create a new character:

1. Click on "Create New Character" in the sidebar
2. Fill in the character details:
   - Name: The character's name
   - Personality Traits: Description of the character's personality
   - Backstory: The character's background story
   - Avatar URL: Link to an image for the character (optional)
3. Click "Create Character"

## API Integration

This application uses the OpenRouter.ai API to access various language models. You'll need to provide your own API key to use the application.

## Customization

You can customize the application by:

- Adding more pre-defined characters in the `sample_characters.json` file
- Modifying the UI styling in the CSS section of `main.py`
- Adding additional model parameters in the sidebar

## License

This project is open source and available under the MIT License.

## Acknowledgements

- Built with [Streamlit](https://streamlit.io/)
- Powered by [OpenRouter.ai](https://openrouter.ai/)