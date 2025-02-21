import os
import json
from dotenv import load_dotenv
import requests
from huggingface_hub import hf_hub_download
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
        """Load personas from the PersonaHub dataset"""
        try:
            # Download the PersonaHub dataset from HuggingFace
            file_path = hf_hub_download(
                repo_id="proj-persona/PersonaHub",
                filename="personas.json",
                repo_type="dataset"
            )
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading PersonaHub personas: {e}")
            return None

    def generate_ux_persona(self, base_persona):
        """Generate a UX persona using Gemini 2.0 Flash"""
        template = '''Create a detailed UX persona based on the following information:

{persona}

Note:

1. The persona should include the following sections:
   - **Name**: The persona's name.
   - **Demographics**: Age, gender, occupation, education, and location.
   - **Goals**: What the persona aims to achieve.
   - **Frustrations**: Pain points and challenges faced by the persona.
   - **Behaviors**: Typical actions and habits.
   - **Motivations**: What drives the persona to achieve their goals.
   - **Technological Proficiency**: The persona's comfort level with technology.
   - **Preferred Channels**: How the persona prefers to communicate and receive information.
2. Your response should start with "Persona:".
3. Ensure the persona is realistic and can be used for UX design purposes.
'''
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful UX researcher who creates detailed user personas."
            },
            {
                "role": "user",
                "content": template.format(persona=base_persona)
            }
        ]

        try:
            logger.info(f"Sending request to OpenRouter API with persona: {base_persona[:50]}...")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "google/gemini-2.0-flash-001",
                    "messages": messages
                }
            )
            response.raise_for_status()
            logger.info("Successfully received response from OpenRouter API")
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating UX persona: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response text: {e.response.text}")
            raise Exception(f"Failed to generate UX persona: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
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
