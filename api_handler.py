import requests
import json
import time

class OpenRouterAPI:
    """Class to handle API requests to OpenRouter.ai"""
    
    def __init__(self, api_key):
        """Initialize with API key"""
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:8501",  # For OpenRouter attribution
            "X-Title": "AI Character Chat"  # For OpenRouter attribution
        }
    
    def get_response(self, messages, model="deepseek/deepseek-chat", temperature=0.7, max_tokens=1000):
        """Get a response from the OpenRouter API
        
        Args:
            messages (list): List of message objects with role and content
            model (str): Model identifier for OpenRouter
            temperature (float): Temperature parameter for generation
            max_tokens (int): Maximum tokens to generate
            
        Returns:
            dict: Response text, token usage, and cost estimate or error message
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Try up to 3 times with exponential backoff
        max_retries = 3
        retry_delay = 1  # Start with 1 second delay
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()  # Raise exception for 4XX/5XX responses
                
                data = response.json()
                
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    
                    # Extract token usage information
                    usage = {
                        "prompt_tokens": data["usage"]["prompt_tokens"],
                        "completion_tokens": data["usage"]["completion_tokens"],
                        "total_tokens": data["usage"]["total_tokens"]
                    }
                    
                    # Calculate estimated cost based on model
                    # These are approximate rates, actual billing may vary
                    cost_per_1m_tokens = {
                        "deepseek/deepseek-chat": 0.50,  # $0.50 per 1M tokens
                        "openai/gpt-4o": 5.00,          # $5.00 per 1M tokens
                        "openai/gpt-4o-mini": 0.80,     # $0.80 per 1M tokens
                        "anthropic/claude-3.5-sonnet": 3.00,  # $3.00 per 1M tokens
                        "mistralai/mistral-7b-instruct": 0.20,  # $0.20 per 1M tokens
                        "meta-llama/llama-3.1-8b-instruct": 0.20  # $0.20 per 1M tokens
                    }
                    
                    # Get cost for this model or default to $1.00 if unknown
                    model_cost = cost_per_1m_tokens.get(model, 1.00)
                    
                    # Calculate estimated cost in dollars
                    estimated_cost = (usage["total_tokens"] / 1000000) * model_cost
                    
                    return {
                        "content": content,
                        "usage": usage,
                        "estimated_cost": estimated_cost
                    }
                else:
                    print(f"Unexpected API response format: {data}")
                    return {"error": "Unexpected API response format"}
                    
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                error_data = {}
                
                try:
                    error_data = e.response.json()
                except:
                    error_data = {"message": str(e)}
                
                # Handle rate limiting
                if status_code == 429:  # Too Many Requests
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        print(f"Rate limited. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        return {"error": "Error: Rate limited. Please try again later."}
                
                # Handle authentication errors
                elif status_code == 401:  # Unauthorized
                    return {"error": "Error: Invalid API key. Please check your OpenRouter API key."}
                
                # Handle other errors
                else:
                    error_message = error_data.get('message', str(e))
                    return {"error": f"Error: {error_message}"}
                    
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    print(f"Connection error. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    return {"error": "Error: Could not connect to OpenRouter API. Please check your internet connection."}
                    
            except Exception as e:
                return {"error": f"Error: {str(e)}"}
        
        return {"error": "Error: Failed to get response after multiple attempts."}
    
    def get_available_models(self):
        """Get a list of available models from OpenRouter
        
        Returns:
            list: List of model objects or None if there was an error
        """
        url = f"{self.base_url}/models"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if 'data' in data:
                return data['data']
            else:
                print(f"Unexpected API response format: {data}")
                return None
                
        except Exception as e:
            print(f"Error getting available models: {str(e)}")
            return None
    
    def validate_api_key(self):
        """Validate the API key by making a simple request
        
        Returns:
            bool: True if the API key is valid, False otherwise
        """
        # Try to get models as a simple validation
        models = self.get_available_models()
        return models is not None
        
    def test_connection(self):
        """Test the connection to the OpenRouter API with a simple message
        
        Returns:
            dict: Response data or error message
        """
        try:
            # Simple test message
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, this is a test message to verify the API connection."}
            ]
            
            response_data = self.get_response(
                messages=test_messages,
                model="deepseek/deepseek-chat",  # Using DeepSeek as specified
                temperature=0.7,
                max_tokens=50  # Small response for quick test
            )
            
            if "error" not in response_data:
                return {
                    "success": True, 
                    "message": "Connection successful", 
                    "response": response_data["content"],
                    "usage": response_data["usage"],
                    "estimated_cost": response_data["estimated_cost"]
                }
            else:
                return {"success": False, "message": response_data["error"] or "Unknown error"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}