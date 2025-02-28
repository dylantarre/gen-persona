import os
import json
from dotenv import load_dotenv
import requests
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PersonaGenerator:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not found in environment variables")
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/gen-persona",
        }
        # Initialize name cache to avoid repetition
        self.name_cache = set()
        self.first_name_cache = set()
        logger.info("PersonaGenerator initialized with API key")

    def load_personas(self):
        """Load personas from local persona.jsonl file"""
        try:
            local_personas = []
            with open('persona.jsonl', 'r') as f:
                for line in f:
                    if line.strip():
                        local_personas.append(json.loads(line)["persona"])
            
            if local_personas:
                logger.info(f"Successfully loaded {len(local_personas)} personas from local file")
                return local_personas
            else:
                logger.warning("Local persona.jsonl file is empty")
        except Exception as e:
            logger.error(f"Error loading local persona file: {e}")
        
        # Use hardcoded fallback personas as last resort
        fallback_personas = [
            "A 35-year-old marketing manager who struggles with work-life balance.",
            "A 28-year-old software engineer who loves building side projects.",
            "A 42-year-old teacher who is hesitant about adopting new technology.",
            "A 19-year-old college student who is always on social media.",
            "A 55-year-old small business owner looking to expand their online presence."
        ]
        logger.info("Using hardcoded fallback personas")
        return fallback_personas

    def generate_ux_persona(self, base_persona, max_retries=3):
        """Generate a UX persona using Gemini 2.0 Flash with validation and retries"""
        template = '''Create a highly detailed UX persona based on the following information:

{persona}

Return your response as a structured JSON object with the following fields:

```json
{{
    "name": "Full Name",
    "demographics": {{
        "age": "number",
        "gender": "string",
        "occupation": {{
            "title": "string",
            "responsibilities": ["string"]
        }},
        "education": {{
            "level": "string",
            "field": "string"
        }},
        "location": {{
            "city_region": "string",
            "living_situation": "string"
        }},
        "income": {{
            "level": "string",
            "financial_situation": "string"
        }},
        "family_status": "string"
    }},
    "goals": {{
        "professional": ["string"],
        "personal": ["string"],
        "short_term": ["string"],
        "long_term": ["string"]
    }},
    "frustrations": {{
        "daily_workflow": ["string"],
        "technology": ["string"],
        "time_management": ["string"],
        "communication": ["string"],
        "industry_specific": ["string"]
    }},
    "behaviors": {{
        "daily_routine": ["string"],
        "technology_usage": ["string"],
        "social_media": ["string"],
        "shopping_habits": ["string"],
        "decision_making": ["string"],
        "information_seeking": ["string"]
    }},
    "motivations": {{
        "values_beliefs": ["string"],
        "professional_motivators": ["string"],
        "personal_drivers": ["string"],
        "success_vision": "string"
    }},
    "technological_proficiency": {{
        "devices": ["string"],
        "software_apps": ["string"],
        "comfort_level": "string",
        "learning_style": "string"
    }},
    "preferred_channels": {{
        "communication": ["string"],
        "media_consumption": ["string"],
        "product_discovery": ["string"],
        "social_networks": ["string"]
    }},
    "day_in_life": "string",
    "quote": "string"
}}
```

IMPORTANT: Your response MUST include ALL of the fields shown above. Make sure to:
1. Replace all placeholder values with realistic, detailed information based on the persona description
2. Ensure all fields are filled with appropriate content
3. Make the persona realistic, nuanced, and useful for UX design purposes
4. Return ONLY the JSON object without any additional text or explanation
5. Verify that your JSON is valid and complete before submitting
'''
        
        # Define the required fields for validation
        required_fields = [
            "name", 
            "demographics", 
            "goals", 
            "frustrations", 
            "behaviors", 
            "motivations", 
            "technological_proficiency", 
            "preferred_channels", 
            "day_in_life", 
            "quote"
        ]
        
        # Define nested required fields
        nested_required_fields = {
            "demographics": ["age", "gender", "occupation", "education", "location", "income", "family_status"],
            "occupation": ["title", "responsibilities"],
            "education": ["level", "field"],
            "location": ["city_region", "living_situation"],
            "income": ["level", "financial_situation"],
            "goals": ["professional", "personal", "short_term", "long_term"],
            "frustrations": ["daily_workflow", "technology", "time_management", "communication", "industry_specific"],
            "behaviors": ["daily_routine", "technology_usage", "social_media", "shopping_habits", "decision_making", "information_seeking"],
            "motivations": ["values_beliefs", "professional_motivators", "personal_drivers", "success_vision"],
            "technological_proficiency": ["devices", "software_apps", "comfort_level", "learning_style"],
            "preferred_channels": ["communication", "media_consumption", "product_discovery", "social_networks"]
        }
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert UX researcher who creates detailed, realistic user personas based on demographic and behavioral information. Your personas are insightful, nuanced, and immediately useful for product design teams. You always return your responses in valid JSON format with ALL required fields."
            },
            {
                "role": "user",
                "content": template.format(persona=base_persona)
            }
        ]

        # Function to validate JSON structure
        def validate_json(json_obj):
            # Check top-level required fields
            for field in required_fields:
                if field not in json_obj:
                    return False, f"Missing required field: {field}"
            
            # Check nested required fields
            for parent, children in nested_required_fields.items():
                if parent in json_obj:
                    if isinstance(json_obj[parent], dict):
                        for child in children:
                            if child not in json_obj[parent]:
                                return False, f"Missing required field: {parent}.{child}"
                    else:
                        return False, f"Field {parent} should be an object"
                
                # Special case for occupation and education which are nested two levels deep
                if parent == "occupation" or parent == "education" or parent == "location":
                    if "demographics" in json_obj and parent in json_obj["demographics"]:
                        if isinstance(json_obj["demographics"][parent], dict):
                            for child in children:
                                if child not in json_obj["demographics"][parent]:
                                    return False, f"Missing required field: demographics.{parent}.{child}"
                        else:
                            return False, f"Field demographics.{parent} should be an object"
            
            return True, "Validation successful"

        # Try up to max_retries times
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt+1}/{max_retries}: Sending request to OpenRouter API with persona: {base_persona[:50]}...")
                
                # Add retry information to the prompt if this is a retry
                retry_messages = messages.copy()
                if attempt > 0:
                    retry_messages.append({
                        "role": "user",
                        "content": f"Your previous response was missing required fields. Please try again and ensure ALL fields are included in your JSON response. This is attempt {attempt+1} of {max_retries}."
                    })
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": "google/gemini-2.0-flash-001",
                        "messages": retry_messages
                    }
                )
                response.raise_for_status()
                logger.info(f"Attempt {attempt+1}/{max_retries}: Successfully received response from OpenRouter API")
                
                # Get the raw content from the API response
                content = response.json()["choices"][0]["message"]["content"]
                
                # Try to extract JSON if it's wrapped in markdown code blocks
                json_str = content
                if "```json" in content:
                    # Extract the JSON part from the markdown code block
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    # Try with just the generic code block marker
                    json_str = content.split("```")[1].split("```")[0].strip()
                
                try:
                    # Parse the JSON to validate it
                    json_obj = json.loads(json_str)
                    
                    # Validate the JSON structure
                    is_valid, validation_message = validate_json(json_obj)
                    if is_valid:
                        logger.info("JSON validation successful")
                        return json.dumps(json_obj, indent=2)
                    else:
                        logger.warning(f"Attempt {attempt+1}/{max_retries}: JSON validation failed: {validation_message}")
                        if attempt == max_retries - 1:
                            # Last attempt failed, return what we have with a warning
                            logger.error(f"All {max_retries} attempts failed validation. Returning best effort result.")
                            return json.dumps(json_obj, indent=2)
                        # Otherwise continue to the next attempt
                        continue
                except json.JSONDecodeError as e:
                    logger.warning(f"Attempt {attempt+1}/{max_retries}: Failed to parse JSON: {e}")
                    if attempt == max_retries - 1:
                        # Last attempt failed, return raw content
                        logger.error(f"All {max_retries} attempts failed to produce valid JSON. Returning raw content.")
                        return content
                    # Otherwise continue to the next attempt
                    continue
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error generating UX persona: {str(e)}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response text: {e.response.text}")
                raise Exception(f"Failed to generate UX persona: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise
        
        # If we get here, all attempts failed
        raise Exception(f"Failed to generate valid UX persona after {max_retries} attempts")

    def generate_name(self, base_persona):
        """Generate a name and title based on the base persona"""
        # If we have too many cached names, clear some to prevent memory issues
        if len(self.name_cache) > 100:
            self.name_cache = set(random.sample(list(self.name_cache), 50))
        if len(self.first_name_cache) > 100:
            self.first_name_cache = set(random.sample(list(self.first_name_cache), 50))
        
        # Generate a simple seed (just numbers) to avoid format string issues
        seed = str(random.randint(1000, 9999))
        
        # Create template without f-string to avoid nested formatting issues
        template = "Create a realistic American name for the following persona that authentically reflects who they are:\n\n"
        template += base_persona
        template += "\n\nIMPORTANT: Using unique seed \"" + seed + "\" for inspiration, create a name that:\n\n"
        template += "1. Feels authentic to the persona's background, profession, age, and characteristics\n"
        template += "2. Represents the diversity of names you would find in America\n"
        template += "3. Feels natural and believable for this specific persona\n"
        template += "4. Is unique and distinctive\n"
        template += "5. Would be recognizable as an American name (including names from various cultural backgrounds that are common in America)\n\n"
        template += "Return your response in this exact format:\n"
        template += "Name: [Full Name]\n"
        template += "Title: [Short descriptive title that captures their role or key characteristic]\n\n"
        template += "Example:\n"
        template += "Name: John Michael Smith\n"
        template += "Title: Digital Nomad"
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert at creating authentic American names that match personas. You create names that reflect America's diverse population, drawing from various cultural backgrounds represented in the United States. Each name you create is unique while still feeling genuine to the persona's characteristics."
            },
            {
                "role": "user",
                "content": template
            }
        ]

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "google/gemini-2.0-flash-001",
                    "messages": messages
                }
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            
            # Parse the response to extract name and title
            name = ""
            title = ""
            
            for line in content.split('\n'):
                if line.startswith("Name:"):
                    name = line.replace("Name:", "").strip()
                elif line.startswith("Title:"):
                    title = line.replace("Title:", "").strip()
            
            # Check if this name or a similar one has been generated before
            if name in self.name_cache:
                logger.warning(f"Name '{name}' has been generated before, requesting a new one")
                return self.generate_name(base_persona)  # Try again
            
            # Extract first name and check if it's been used before
            first_name = name.split()[0] if name and " " in name else name
            if first_name in self.first_name_cache:
                logger.warning(f"First name '{first_name}' has been used before, requesting a new one")
                return self.generate_name(base_persona)  # Try again
            
            # Add to cache
            self.name_cache.add(name)
            self.first_name_cache.add(first_name)
            
            return {
                "name": name,
                "title": title,
                "base_persona": base_persona  # Include the original persona
            }
        except Exception as e:
            logger.error(f"Error generating name and title: {str(e)}")
            raise

def main():
    generator = PersonaGenerator()
    
    # Load PersonaHub personas
    personas = generator.load_personas()
    if not personas:
        logger.error("Failed to load PersonaHub personas")
        return

    # Generate UX persona for each PersonaHub persona
    for idx, persona in enumerate(personas):
        logger.info(f"Processing persona {idx + 1}/{len(personas)}")
        ux_persona = generator.generate_ux_persona(persona)
        if ux_persona:
            logger.info("Generated UX Persona:")
            logger.info(ux_persona)
            logger.info("\n" + "="*80)

if __name__ == "__main__":
    main()
