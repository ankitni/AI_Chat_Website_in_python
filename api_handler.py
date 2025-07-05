import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_handler.log"),
        logging.StreamHandler()
    ]
)

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
        
        logging.info(f"Making API request to {url} with model: {model}")
        
        # Try up to 3 times with exponential backoff
        max_retries = 3
        retry_delay = 1  # Start with 1 second delay
        
        for attempt in range(max_retries):
            try:
                logging.info(f"API request attempt {attempt+1}/{max_retries}")
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
                        "qwen/qwen3-235b-a22b:free": 0.50,  # $0.50 per 1M tokens
                        "openai/gpt-4o": 5.00,          # $5.00 per 1M tokens
                        "openai/gpt-4o-mini": 0.80,     # $0.80 per 1M tokens
                        "anthropic/claude-3.5-sonnet": 3.00,  # $3.00 per 1M tokens
                        "mistralai/mistral-7b-instruct": 0.20,  # $0.20 per 1M tokens
                        "meta-llama/llama-3.1-8b-instruct": 0.20,  # $0.20 per 1M tokens
                        "01-ai/yi-large": 1.50,         # $1.50 per 1M tokens
                        "thudm/glm-z1-32b:free": 1.00,  # $1.00 per 1M tokens
                        "cognitivecomputations/dolphin3.0-mistral-24b:free": 0.20  # $0.20 per 1M tokens
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
                    error_msg = f"Unexpected API response format: {data}"
                    logging.error(error_msg)
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
                        logging.warning(f"Rate limited. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logging.error("Rate limit exceeded after multiple retries")
                        return {"error": "Error: Rate limited. Please try again later."}
                
                # Handle authentication errors
                elif status_code == 401:  # Unauthorized
                    logging.error(f"Authentication error: Invalid API key for model {model}")
                    return {"error": "Error: Invalid API key. Please check your OpenRouter API key."}
                
                # Handle model not found or invalid model errors
                elif status_code == 404 or status_code == 400:
                    error_message = error_data.get('message', str(e))
                    if "model" in error_message.lower():
                        logging.error(f"Invalid model name: '{model}'. Error: {error_message}")
                        return {"error": f"Error: Invalid model name '{model}'. Please check the model identifier."}
                    else:
                        logging.error(f"API error {status_code}: {error_message}")
                        return {"error": f"Error: {error_message}"}
                
                # Handle other errors
                else:
                    error_message = error_data.get('message', str(e))
                    logging.error(f"API error {status_code}: {error_message}")
                    return {"error": f"Error: {error_message}"}
                    
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    logging.warning(f"Connection error. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logging.error("Connection error after multiple retries")
                    return {"error": "Error: Could not connect to OpenRouter API. Please check your internet connection."}
                    
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                return {"error": f"Error: {str(e)}"}
        
        logging.error("Failed to get response after multiple attempts")
        return {"error": "Error: Failed to get response after multiple attempts."}
    
    def get_available_models(self):
        """Get a list of available models from OpenRouter
        
        Returns:
            list: List of model objects or None if there was an error
        """
        url = f"{self.base_url}/models"
        logging.info(f"Fetching available models from {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if 'data' in data:
                logging.info(f"Successfully retrieved {len(data['data'])} models")
                return data['data']
            else:
                error_msg = f"Unexpected API response format: {data}"
                logging.error(error_msg)
                return None
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            logging.error(f"HTTP error {status_code} when fetching models: {str(e)}")
            return None
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection error when fetching models: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error getting available models: {str(e)}")
            return None
    
    def validate_api_key(self):
        """Validate the API key by making a simple request
        
        Returns:
            bool: True if the API key is valid, False otherwise
        """
        logging.info("Validating API key")
        # Try to get models as a simple validation
        models = self.get_available_models()
        if models is not None:
            logging.info("API key validation successful")
            return True
        else:
            logging.error("API key validation failed")
            return False
        
    def direct_api_request(self, model, messages):
        """Make a direct API request to OpenRouter without any retry logic
        
        Args:
            model (str): Model identifier for OpenRouter
            messages (list): List of message objects with role and content
            
        Returns:
            dict: Raw API response or error details
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 50
        }
        
        logging.info(f"Making direct API request to {url} with model: {model}")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            status_code = response.status_code
            
            try:
                response_json = response.json()
                logging.info(f"Direct API response status: {status_code}, content: {response_json}")
                return {
                    "success": 200 <= status_code < 300,
                    "status_code": status_code,
                    "response": response_json
                }
            except Exception as e:
                logging.error(f"Failed to parse JSON response: {str(e)}")
                return {
                    "success": False,
                    "status_code": status_code,
                    "error": f"Failed to parse response: {str(e)}",
                    "raw_response": response.text
                }
                
        except Exception as e:
            logging.error(f"Exception during direct API request: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_connection(self, model="deepseek/deepseek-chat"):
        """Test the connection to the OpenRouter API with a simple message
        
        Args:
            model (str): Model identifier for OpenRouter (default: deepseek/deepseek-chat)
            
        Returns:
            dict: Response data or error message
        """
        logging.info(f"Testing connection with model: {model}")
        try:
            # Simple test message
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, this is a test message to verify the API connection."}
            ]
            
            logging.info(f"Sending test request to model: {model} with API key: {self.api_key[:5]}...")
            
            # For problematic models, try direct API request and use its result directly
            problematic_models = ["qwen/qwen3-235b-a22b:free", "thudm/glm-z1-32b:free", "cognitivecomputations/dolphin3.0-mistral-24b:free"]
            if model in problematic_models:
                logging.info(f"Using direct API request for potentially problematic model: {model}")
                direct_result = self.direct_api_request(model, test_messages)
                logging.info(f"Direct API request result: {direct_result}")
                
                if direct_result.get("success", False):
                    # Extract content from the direct API response
                    try:
                        content = direct_result.get("response", {}).get("choices", [{}])[0].get("message", {}).get("content", "No content")
                        usage = direct_result.get("response", {}).get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
                        
                        # Calculate estimated cost based on model
                        cost_per_1m_tokens = {
                            "qwen/qwen3-235b-a22b:free": 0.50,
                            "thudm/glm-z1-32b:free": 1.00,
                            "cognitivecomputations/dolphin3.0-mistral-24b:free": 0.20
                        }
                        model_cost = cost_per_1m_tokens.get(model, 1.00)
                        estimated_cost = (usage.get("total_tokens", 0) / 1000000) * model_cost
                        
                        logging.info(f"Test connection successful for problematic model: {model}")
                        return {
                            "success": True, 
                            "message": "Connection successful", 
                            "response": content,
                            "usage": usage,
                            "estimated_cost": estimated_cost
                        }
                    except Exception as e:
                        logging.error(f"Error parsing direct API response for model {model}: {str(e)}")
                        # Fall through to standard get_response method
                else:
                    error_msg = direct_result.get("error", "Unknown error")
                    logging.error(f"Direct API request failed for model: {model}. Error: {error_msg}")
                    return {"success": False, "message": f"Error: {error_msg}"}
            
            # Standard approach for non-problematic models or as fallback
            response_data = self.get_response(
                messages=test_messages,
                model=model,  # Using the specified model
                temperature=0.7,
                max_tokens=50  # Small response for quick test
            )
            
            if "error" not in response_data:
                logging.info(f"Test connection successful for model: {model}")
                return {
                    "success": True, 
                    "message": "Connection successful", 
                    "response": response_data["content"],
                    "usage": response_data["usage"],
                    "estimated_cost": response_data["estimated_cost"]
                }
            else:
                error_msg = response_data["error"] or "Unknown error"
                logging.error(f"Test connection failed for model: {model}. Error: {error_msg}")
                return {"success": False, "message": error_msg}
                
        except Exception as e:
            logging.error(f"Exception during test connection for model: {model}. Error: {str(e)}")
            return {"success": False, "message": str(e)}