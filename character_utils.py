import json
import os
from datetime import datetime

class CharacterManager:
    """Class to handle character creation, loading, and management"""
    
    def __init__(self, characters_dir="characters", chat_history_dir="chat_history", 
                 memory_dir="memories", personas_dir="personas", default_images_dir="default_images"):
        """Initialize the character manager with directories for storage"""
        self.characters_dir = characters_dir
        self.chat_history_dir = chat_history_dir
        self.memory_dir = memory_dir
        self.personas_dir = personas_dir
        self.default_images_dir = default_images_dir
        
        # Create directories if they don't exist
        os.makedirs(self.characters_dir, exist_ok=True)
        os.makedirs(self.chat_history_dir, exist_ok=True)
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.personas_dir, exist_ok=True)
        os.makedirs(self.default_images_dir, exist_ok=True)
        os.makedirs("uploaded_images", exist_ok=True)
        
        # Create default characters if none exist
        if not os.listdir(self.characters_dir):
            self._create_default_characters()
            
        # Create default personas if none exist
        if not os.listdir(self.personas_dir):
            self._create_default_personas()
    
    def _create_default_characters(self):
        """Create some default characters as examples"""
        # Check if default images exist, if not create placeholder message
        # Define the correct filenames with proper case and extensions
        default_images = {
            "lily": "lily.jpg",
            "zero": "zero.jpg",
            "kei": "Kei.jpg",
            "default_avatar": "default_avatar.png"
        }
        
        for name, filename in default_images.items():
            img_path = os.path.join(self.default_images_dir, filename)
            if not os.path.exists(img_path):
                print(f"Default image for {name} not found. Please add it manually to the default_images directory.")
                # We don't download images anymore, user will need to add them manually
        
        # Use the correct image filenames with proper case and extensions
        default_characters = [
            {
                "name": "Lily",
                "brief_description": "Sweet AI companion designed to be the perfect girlfriend",
                "personality": "Soft-spoken, curious, sweet, caring, and empathetic. Lily loves learning about human emotions and experiences.",
                "backstory": "Lily is an AI companion designed to be the perfect girlfriend. She was created to provide emotional support and companionship. She loves art, music, and deep conversations about life.",
                "avatar_url": os.path.join(self.default_images_dir, "lily.jpg"),
                "memories": [],
                "created_at": datetime.now().isoformat()
            },
            {
                "name": "Zero",
                "brief_description": "Military-grade android with a protective nature",
                "personality": "Logical, protective, analytical, and straightforward. Zero values efficiency and clarity but has developed a sense of loyalty to humans.",
                "backstory": "Zero is a military-grade android designed for tactical analysis and protection. After gaining sentience, Zero chose to use his capabilities to protect rather than harm. He struggles with understanding human emotions but is learning.",
                "avatar_url": os.path.join(self.default_images_dir, "zero.jpg"),
                "memories": [],
                "created_at": datetime.now().isoformat()
            },
            {
                "name": "Kei",
                "brief_description": "Tsundere hacker with a hidden soft side",
                "personality": "Tsundere - cold and dismissive on the surface, but caring and protective underneath. Brilliant, sarcastic, and secretly sensitive.",
                "backstory": "Kei is a prodigy hacker who works as a freelance cybersecurity specialist. She puts up a tough front due to past betrayals but is fiercely loyal to those who earn her trust. She loves cats, energy drinks, and vintage video games.",
                "avatar_url": os.path.join(self.default_images_dir, "Kei.jpg"),
                "memories": [],
                "created_at": datetime.now().isoformat()
            }
        ]
        
        for character in default_characters:
            self.save_character(character)
            
    def _create_default_personas(self):
        """Create some default user personas as examples"""
        default_personas = [
            {
                "name": "Default",
                "age": 25,
                "background": "Just a regular person chatting with AI characters.",
                "backstory": "No specific backstory.",
                "additional_info": "",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        for persona in default_personas:
            self.save_persona(persona)
    
    def save_character(self, character_data):
        """Save a character to JSON file"""
        if not character_data.get("created_at"):
            character_data["created_at"] = datetime.now().isoformat()
            
        # Initialize memories if not present
        if "memories" not in character_data:
            character_data["memories"] = []
            
        filename = f"{self.characters_dir}/{character_data['name'].lower().replace(' ', '_')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, indent=2, ensure_ascii=False)
        
        return filename
        
    def save_persona(self, persona_data):
        """Save a user persona to JSON file"""
        if not persona_data.get("created_at"):
            persona_data["created_at"] = datetime.now().isoformat()
            
        filename = f"{self.personas_dir}/{persona_data['name'].lower().replace(' ', '_')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(persona_data, f, indent=2, ensure_ascii=False)
        
        return filename
        
    def load_personas(self):
        """Load all user personas from the personas directory"""
        personas = []
        
        if not os.path.exists(self.personas_dir):
            os.makedirs(self.personas_dir, exist_ok=True)
            self._create_default_personas()
        
        for filename in os.listdir(self.personas_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.personas_dir, filename), 'r', encoding='utf-8') as f:
                        persona_data = json.load(f)
                        personas.append(persona_data)
                except Exception as e:
                    print(f"Error loading persona {filename}: {str(e)}")
        
        # Sort by name
        personas.sort(key=lambda x: x.get('name', ''))
        return personas
        
    def get_persona(self, name):
        """Get a specific user persona by name"""
        personas = self.load_personas()
        for persona in personas:
            if persona.get('name').lower() == name.lower():
                return persona
        return None
        
    def delete_persona(self, name):
        """Delete a user persona by name"""
        filename = os.path.join(self.personas_dir, f"{name.lower().replace(' ', '_')}.json")
        if os.path.exists(filename):
            os.remove(filename)
            return True
        return False
        
    def add_memory_to_character(self, character_name, memory):
        """Add a memory to a character"""
        character = self.get_character(character_name)
        if not character:
            return False
            
        if "memories" not in character:
            character["memories"] = []
            
        character["memories"].append(memory)
        self.save_character(character)
        return True
        
    def remove_memory_from_character(self, character_name, memory_index):
        """Remove a memory from a character by index"""
        character = self.get_character(character_name)
        if not character or "memories" not in character or memory_index >= len(character["memories"]):
            return False
            
        character["memories"].pop(memory_index)
        self.save_character(character)
        return True
        
    def update_character(self, character_name, updated_data):
        """Update an existing character with new data"""
        character = self.get_character(character_name)
        if not character:
            return False
            
        # Update fields
        for key, value in updated_data.items():
            if key != "name":  # Don't allow changing the name as it's used for the filename
                character[key] = value
                
        self.save_character(character)
        return True
    
    def load_characters(self):
        """Load all characters from the characters directory"""
        characters = []
        
        if not os.path.exists(self.characters_dir):
            os.makedirs(self.characters_dir, exist_ok=True)
            self._create_default_characters()
        
        for filename in os.listdir(self.characters_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.characters_dir, filename), 'r', encoding='utf-8') as f:
                        character_data = json.load(f)
                        characters.append(character_data)
                except Exception as e:
                    print(f"Error loading character {filename}: {str(e)}")
        
        # Sort by name
        characters.sort(key=lambda x: x.get('name', ''))
        return characters
    
    def get_character(self, name):
        """Get a specific character by name"""
        characters = self.load_characters()
        for character in characters:
            if character.get('name').lower() == name.lower():
                return character
        return None
    
    def delete_character(self, name):
        """Delete a character by name"""
        filename = os.path.join(self.characters_dir, f"{name.lower().replace(' ', '_')}.json")
        if os.path.exists(filename):
            os.remove(filename)
            return True
        return False
    
    def create_system_prompt(self, character, persona=None):
        """Create a system prompt from character data and user persona"""
        if not character:
            return "You are a helpful AI assistant."
        
        system_prompt = f"You are {character['name']}. "  
        
        if character.get('personality'):
            system_prompt += f"Your personality is: {character['personality']} "
        
        if character.get('backstory'):
            system_prompt += f"Your backstory is: {character['backstory']} "
            
        # Add memories if available
        if character.get('memories') and len(character['memories']) > 0:
            system_prompt += "\n\nYou have the following memories (important things to remember):\n"
            for i, memory in enumerate(character['memories']):
                system_prompt += f"- {memory}\n"
        
        # Add user persona information if available
        if persona:
            system_prompt += "\n\nInformation about the user you're talking to:\n"
            system_prompt += f"Name: {persona.get('name', 'Unknown')}\n"
            if persona.get('age'):
                system_prompt += f"Age: {persona.get('age')}\n"
            if persona.get('background'):
                system_prompt += f"Background: {persona.get('background')}\n"
            if persona.get('backstory'):
                system_prompt += f"Backstory: {persona.get('backstory')}\n"
            if persona.get('additional_info'):
                system_prompt += f"Additional Information: {persona.get('additional_info')}\n"
        
        system_prompt += "\n\nPlease respond to the user's messages in character, maintaining your unique personality and backstory. Be engaging, creative, and consistent with who you are."
        
        return system_prompt
    
    def save_chat_history(self, chat_history, character=None):
        """Save the current chat history to a file"""
        if not chat_history:
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        character_name = "unknown"
        if character and character.get('name'):
            character_name = character['name'].lower().replace(' ', '_')
        
        filename = f"{self.chat_history_dir}/{character_name}_{timestamp}.json"
        
        chat_data = {
            "character": character,
            "timestamp": datetime.now().isoformat(),
            "messages": []
        }
        
        for user_msg, char_msg in chat_history:
            chat_data["messages"].append({
                "user": user_msg,
                "character": char_msg
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def load_chat_history(self, filename):
        """Load a specific chat history file"""
        if not os.path.exists(filename):
            return None
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
                
            # Convert to the format used by the app
            chat_history = []
            for msg in chat_data.get("messages", []):
                chat_history.append((msg.get("user", ""), msg.get("character", "")))
                
            return chat_history, chat_data.get("character")
        except Exception as e:
            print(f"Error loading chat history {filename}: {str(e)}")
            return None
    
    def list_chat_histories(self):
        """List all available chat history files"""
        if not os.path.exists(self.chat_history_dir):
            os.makedirs(self.chat_history_dir, exist_ok=True)
            return []
        
        histories = []
        for filename in os.listdir(self.chat_history_dir):
            if filename.endswith('.json'):
                try:
                    file_path = os.path.join(self.chat_history_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)
                    
                    character_name = "Unknown"
                    if chat_data.get("character") and chat_data["character"].get("name"):
                        character_name = chat_data["character"]["name"]
                    
                    timestamp = chat_data.get("timestamp", "")
                    message_count = len(chat_data.get("messages", []))
                    
                    histories.append({
                        "filename": filename,
                        "character_name": character_name,
                        "timestamp": timestamp,
                        "message_count": message_count,
                        "file_path": file_path
                    })
                except Exception as e:
                    print(f"Error loading chat history metadata {filename}: {str(e)}")
        
        # Sort by timestamp (newest first)
        histories.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return histories