import os
import json
from dotenv import load_dotenv
import requests
import logging

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
    "age": 30,
    "gender": "Gender",
    "occupation": {{
      "title": "Job Title",
      "responsibilities": ["Responsibility 1", "Responsibility 2"]
    }},
    "education": {{
      "level": "Education Level",
      "field": "Field of Study"
    }},
    "location": {{
      "city": "City/Region",
      "living_situation": "Living Situation"
    }},
    "income": "Income Level",
    "family_status": "Family Status"
  }},
  "goals": {{
    "professional": ["Professional Goal 1", "Professional Goal 2"],
    "personal": ["Personal Goal 1", "Personal Goal 2"],
    "short_term": ["Short-term Goal 1", "Short-term Goal 2"],
    "long_term": ["Long-term Goal 1", "Long-term Goal 2"]
  }},
  "frustrations": {{
    "workflow": ["Workflow Pain Point 1", "Workflow Pain Point 2"],
    "technology": ["Technology Challenge 1", "Technology Challenge 2"],
    "time_management": ["Time Management Issue 1", "Time Management Issue 2"],
    "communication": ["Communication Barrier 1", "Communication Barrier 2"],
    "industry_specific": ["Industry Frustration 1", "Industry Frustration 2"]
  }},
  "behaviors": {{
    "daily_routine": ["Routine Item 1", "Routine Item 2"],
    "technology_usage": ["Technology Usage Pattern 1", "Technology Usage Pattern 2"],
    "social_media": ["Social Media Behavior 1", "Social Media Behavior 2"],
    "shopping_habits": ["Shopping Habit 1", "Shopping Habit 2"],
    "decision_making": ["Decision Process 1", "Decision Process 2"],
    "information_seeking": ["Information Seeking Behavior 1", "Information Seeking Behavior 2"]
  }},
  "motivations": {{
    "values": ["Value 1", "Value 2"],
    "professional_motivators": ["Professional Motivator 1", "Professional Motivator 2"],
    "personal_drivers": ["Personal Driver 1", "Personal Driver 2"],
    "success_metrics": ["Success Metric 1", "Success Metric 2"]
  }},
  "tech_proficiency": {{
    "devices": ["Device 1", "Device 2"],
    "software": ["Software 1", "Software 2"],
    "comfort_level": "Comfort Level Description",
    "learning_style": "Learning Style Description"
  }},
  "preferred_channels": {{
    "communication": ["Communication Channel 1", "Communication Channel 2"],
    "media_consumption": ["Media Channel 1", "Media Channel 2"],
    "product_discovery": ["Discovery Channel 1", "Discovery Channel 2"],
    "social_networks": ["Social Network 1", "Social Network 2"]
  }},
  "day_in_life": "A brief narrative of their typical day from morning to evening.",
  "quote": "A representative quote that captures their attitude or perspective."
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
            "tech_proficiency", 
            "preferred_channels", 
            "day_in_life", 
            "quote"
        ]
        
        # Define nested required fields
        nested_required_fields = {
            "demographics": ["age", "gender", "occupation", "education", "location", "income", "family_status"],
            "occupation": ["title", "responsibilities"],
            "education": ["level", "field"],
            "location": ["city", "living_situation"],
            "goals": ["professional", "personal", "short_term", "long_term"],
            "frustrations": ["workflow", "technology", "time_management", "communication", "industry_specific"],
            "behaviors": ["daily_routine", "technology_usage", "social_media", "shopping_habits", "decision_making", "information_seeking"],
            "motivations": ["values", "professional_motivators", "personal_drivers", "success_metrics"],
            "tech_proficiency": ["devices", "software", "comfort_level", "learning_style"],
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
