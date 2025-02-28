import os
import json
from dotenv import load_dotenv
import requests
import logging
import random
import time

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
        
        # Add a retry counter to prevent infinite loops
        max_retries = 5
        retry_count = 0
        
        # First, restate the base_persona with different phrasing but same meaning
        restated_persona = self._restate_persona(base_persona)
        
        while retry_count < max_retries:
            # Generate a more complex seed using multiple factors
            persona_hash = hash(base_persona) % 10000
            timestamp = int(time.time() * 1000) % 10000
            random_component = random.randint(10000, 99999)
            seed = f"{persona_hash}-{random_component}-{timestamp}-{random.choice(['A','B','C','D','E','F'])}"
            
            # Create template without f-string to avoid nested formatting issues
            template = "Create a realistic American name for the following persona that authentically reflects who they are:\n\n"
            template += restated_persona  # Use the restated persona instead of the original
            template += "\n\nIMPORTANT: Using unique seed \"" + seed + "\" for inspiration, create a name that:\n\n"
            template += "1. Feels authentic to the persona's background, profession, age, and characteristics\n"
            template += "2. Represents the diversity of names you would find in America\n"
            template += "3. Feels natural and believable for this specific persona\n"
            template += "4. Is unique and distinctive\n"
            template += "5. Would be recognizable as an American name (including names from various cultural backgrounds that are common in America)\n\n"
            
            # Add a note about uniqueness and specifically mention problematic names
            template += "IMPORTANT: Please be creative and generate a truly unique name. The system has already generated many names, so try to create something fresh and different.\n\n"
            template += "NOTE: The names 'Anya', 'Serena', 'Rohan', 'Indira', 'Hollis', 'Seraphina', and 'Zoya' have been used too frequently. Please avoid these names and create something different.\n\n"
            
            # Add extensive examples of diverse American names to inspire variety
            template += "Here are examples of diverse American names for inspiration (DO NOT use these exact names, create new ones):\n\n"
            
            # Common American names
            template += "Common American names:\n"
            template += "- James Wilson, Emma Taylor, Michael Anderson, Sophia Thomas\n"
            template += "- David Jackson, Jennifer White, Robert Harris, Linda Martin\n"
            template += "- William Thompson, Elizabeth Garcia, Richard Martinez, Patricia Robinson\n\n"
            
            # Hispanic/Latino American names
            template += "Hispanic/Latino American names:\n"
            template += "- Miguel Diaz, Sofia Fernandez, Carlos Flores, Isabella Gomez\n"
            template += "- Jose Gutierrez, Elena Hernandez, Luis Lopez, Gabriela Martinez\n"
            template += "- Antonio Morales, Valentina Ortiz, Francisco Perez, Camila Ramirez\n"
            template += "- Alejandro Sanchez, Carmen Vasquez, Javier Rodriguez, Lucia Torres\n\n"
            
            # Asian American names
            template += "Asian American names:\n"
            template += "- Wei Zhang, Mei Chen, Li Liu, Jing Wang\n"
            template += "- Hiroshi Tanaka, Yuki Suzuki, Takashi Yamamoto, Sakura Nakamura\n"
            template += "- Sanjay Gupta, Priya Sharma, Raj Patel, Lakshmi Desai\n"
            template += "- Jin Park, Min Lee, Seung Choi, Ji Kang\n"
            template += "- Anh Nguyen, Binh Tran, Minh Pham, Linh Vo\n"
            template += "- Mei-Ling Wu, Tao Yang, Xiu Huang, Feng Zhou\n\n"
            
            # Middle Eastern/North African American names
            template += "Middle Eastern/North African American names:\n"
            template += "- Omar Ali, Fatima Khan, Ali Ahmed, Leila Hassan\n"
            template += "- Mohammed Ibrahim, Yasmin Mahmoud, Ahmed Abadi, Nadia El-Amin\n"
            template += "- Zara Abboud, Karim Najjar, Layla Hakim, Tariq Masri\n\n"
            
            # African American names
            template += "African American names:\n"
            template += "- Jamal Washington, Keisha Jefferson, Darnell Banks, Latoya Booker\n"
            template += "- Tyrone Coleman, Shaniqua Dixon, DeAndre Freeman, Imani Gaines\n"
            template += "- Marcus Johnson, Aaliyah Williams, Terrell Davis, Ebony Wilson\n"
            template += "- Darius Smith, Aisha Thompson, Malik Jackson, Tiana Harris\n\n"
            
            # European American names
            template += "European American names:\n"
            template += "- Giovanni Rossi, Isabella Bianchi, Dmitri Ivanov, Natasha Petrov\n"
            template += "- Hans Muller, Ingrid Weber, Pierre Dubois, Sophie Moreau\n"
            template += "- Sven Johansson, Astrid Lindgren, Klaus Schmidt, Brigitte Hoffmann\n"
            template += "- Liam O'Connor, Siobhan Murphy, Declan Kelly, Fiona Byrne\n\n"
            
            # Jewish American names
            template += "Jewish American names:\n"
            template += "- Ari Cohen, Rachel Goldberg, Moshe Friedman, Leah Shapiro\n"
            template += "- Eli Levy, Sarah Katz, Isaac Stern, Rebecca Rosen\n"
            template += "- Benjamin Abramowitz, Hannah Silverman, Noah Greenberg, Esther Finkelstein\n\n"
            
            # Native American names
            template += "Native American names:\n"
            template += "- Koda Blackhawk, Aiyana Eagleheart, Bodaway Redhorse, Halona Thundercloud\n"
            template += "- Chayton Whitefeather, Nayeli Rainwater, Takoda Strongbow, Winona Skyhawk\n\n"
            
            # Pacific Islander American names
            template += "Pacific Islander American names:\n"
            template += "- Kekoa Kalani, Leilani Kealoha, Keanu Mahelona, Moana Nainoa\n"
            template += "- Kai Akamu, Alana Kahale, Malie Kanoa, Nohea Palakiko\n\n"
            
            # Additional diverse names
            template += "Additional diverse names:\n"
            template += "- Amara Okafor, Kwame Mensah, Chioma Adebayo, Oluchi Eze\n"
            template += "- Arjun Mehta, Divya Chadha, Vikram Malhotra, Ananya Reddy\n"
            template += "- Thuy Phan, Quang Dang, Hien Bui, Tuyet Duong\n"
            template += "- Cheng-Wei Lin, Mei-Xiu Huang, Jian-Yong Zhao, Xiao-Ling Tang\n\n"
            
            template += "Return your response in this exact format:\n"
            template += "Name: [Full Name]\n"
            template += "Title: [Short descriptive title that captures their role or key characteristic]\n\n"
            template += "Example:\n"
            template += "Name: John Michael Smith\n"
            template += "Title: Digital Nomad"
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at creating authentic American names that match personas. You create names that reflect America's diverse population, drawing from various cultural backgrounds represented in the United States. Each name you create is unique while still feeling genuine to the persona's characteristics. You never repeat names you've created before. You are especially good at creating fresh, original names that haven't been used before."
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
                        "messages": messages,
                        "temperature": 1.0  # Increase temperature for more randomness
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
                    logger.warning(f"Name '{name}' has been generated before, retry {retry_count+1}/{max_retries}")
                    retry_count += 1
                    continue
                
                # Extract first name and check if it's been used before
                first_name = name.split()[0] if name and " " in name else name
                if first_name in self.first_name_cache:
                    logger.warning(f"First name '{first_name}' has been used before, retry {retry_count+1}/{max_retries}")
                    retry_count += 1
                    continue
                
                # Add to cache
                self.name_cache.add(name)
                self.first_name_cache.add(first_name)
                
                return {
                    "name": name,
                    "title": title,
                    "base_persona": restated_persona  # Include the restated persona instead of original
                }
            except Exception as e:
                logger.error(f"Error generating name and title: {str(e)}")
                retry_count += 1
        
        # If we've exhausted all retries, generate a completely random name
        logger.warning(f"Exhausted all {max_retries} retries, generating a fallback name")
        
        # List of diverse first and last names to use as fallback - EXPANDED
        first_names = [
            # Common American names
            "Michael", "Sarah", "David", "Jennifer", "James", "Maria", "Robert", "Linda", "William", "Elizabeth", 
            "Richard", "Patricia", "Joseph", "Susan", "Thomas", "Jessica", "Charles", "Margaret", "Daniel", "Karen",
            "Matthew", "Nancy", "Anthony", "Lisa", "Mark", "Betty", "Donald", "Dorothy", "Steven", "Sandra",
            "Paul", "Ashley", "Andrew", "Kimberly", "Joshua", "Donna", "Kenneth", "Emily", "Kevin", "Michelle",
            "Brian", "Amanda", "George", "Melissa", "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca",
            "Jason", "Laura", "Jeffrey", "Sharon", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
            "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna", "Larry", "Brenda",
            # Additional diverse names
            "Miguel", "Sofia", "Carlos", "Isabella", "Jose", "Elena", "Luis", "Gabriela", "Antonio", "Valentina",
            "Wei", "Mei", "Li", "Jing", "Hiroshi", "Yuki", "Takashi", "Sakura", "Sanjay", "Priya",
            "Raj", "Lakshmi", "Jin", "Min", "Seung", "Ji", "Omar", "Fatima", "Ali", "Leila",
            "Mohammed", "Yasmin", "Ahmed", "Nadia", "Jamal", "Keisha", "Darnell", "Latoya", "Tyrone", "Shaniqua",
            "Giovanni", "Isabella", "Dmitri", "Natasha", "Hans", "Ingrid", "Pierre", "Sophie", "Ari", "Rachel",
            "Moshe", "Leah", "Eli", "Sarah", "Isaac", "Rebecca", "Koda", "Aiyana", "Bodaway", "Halona",
            "Kekoa", "Leilani", "Keanu", "Moana", "Amara", "Kwame", "Chioma", "Oluchi", "Arjun", "Divya",
            "Vikram", "Ananya", "Thuy", "Quang", "Hien", "Tuyet", "Cheng", "Mei-Xiu", "Jian", "Xiao"
        ]
        
        last_names = [
            # Common American last names
            "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
            "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson",
            "Clark", "Rodriguez", "Lewis", "Lee", "Walker", "Hall", "Allen", "Young", "Hernandez", "King",
            "Wright", "Lopez", "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson", "Carter",
            "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards", "Collins",
            "Stewart", "Sanchez", "Morris", "Rogers", "Reed", "Cook", "Morgan", "Bell", "Murphy", "Bailey",
            "Rivera", "Cooper", "Richardson", "Cox", "Howard", "Ward", "Torres", "Peterson", "Gray", "Ramirez",
            # Additional diverse last names
            "Diaz", "Fernandez", "Flores", "Gomez", "Gutierrez", "Hernandez", "Lopez", "Martinez", "Morales", "Ortiz",
            "Zhang", "Chen", "Liu", "Wang", "Tanaka", "Suzuki", "Yamamoto", "Nakamura", "Gupta", "Sharma",
            "Patel", "Desai", "Park", "Lee", "Choi", "Kang", "Ali", "Khan", "Ahmed", "Hassan",
            "Ibrahim", "Mahmoud", "Abadi", "El-Amin", "Washington", "Jefferson", "Banks", "Booker", "Coleman", "Dixon",
            "Rossi", "Bianchi", "Ivanov", "Petrov", "Muller", "Weber", "Dubois", "Moreau", "Cohen", "Goldberg",
            "Friedman", "Shapiro", "Levy", "Katz", "Stern", "Rosen", "Blackhawk", "Eagleheart", "Redhorse", "Thundercloud",
            "Kalani", "Kealoha", "Mahelona", "Nainoa", "Okafor", "Mensah", "Adebayo", "Eze", "Mehta", "Chadha",
            "Malhotra", "Reddy", "Phan", "Dang", "Bui", "Duong", "Lin", "Huang", "Zhao", "Tang"
        ]
        
        # Generate a random name
        random_first = random.choice(first_names)
        random_last = random.choice(last_names)
        
        # Make sure we don't use a first name that's already in the cache
        attempts = 0
        while random_first in self.first_name_cache and attempts < 10:
            random_first = random.choice(first_names)
            attempts += 1
        
        # If we still can't find a unique name after 10 attempts, just use what we have
        # This prevents infinite loops in extreme cases
        if attempts >= 10:
            logger.warning("Could not find a unique first name after 10 attempts, using a potentially repeated name")
        
        random_name = f"{random_first} {random_last}"
        
        # Add to cache
        self.name_cache.add(random_name)
        self.first_name_cache.add(random_first)
        
        # Generate a generic title based on the persona
        title = "Professional"
        if "teacher" in base_persona.lower() or "education" in base_persona.lower():
            title = "Educator"
        elif "engineer" in base_persona.lower() or "developer" in base_persona.lower():
            title = "Tech Professional"
        elif "market" in base_persona.lower():
            title = "Marketing Specialist"
        elif "business" in base_persona.lower():
            title = "Business Owner"
        elif "student" in base_persona.lower():
            title = "Student"
        
        return {
            "name": random_name,
            "title": title,
            "base_persona": restated_persona  # Include the restated persona instead of original
        }
        
    def _restate_persona(self, base_persona):
        """Restate the base persona with different phrasing but same meaning"""
        # Use the API to restate the persona
        template = "Restate the following persona description in a single, natural sentence that a UX researcher might jot down in their notes. Keep the same meaning and all key details about age, profession, and characteristics:\n\n"
        template += base_persona
        template += "\n\nIMPORTANT: Your response should be ONLY ONE SENTENCE. No prefacing text, no explanations, no bullet points. Write it as a human would naturally take a quick note. Start directly with the restated description."
        template += "\n\nCRITICAL: The description MUST be about a PERSON, never a company, business, or organization. If the input describes a business, convert it to describe a person who works at or owns that business instead. ALWAYS describe an individual human being with personal characteristics."
        template += "\n\nEXAMPLES OF CONVERSION:"
        template += "\nInput: 'This is a business incubator offering office space and mentorship.'"
        template += "\nOutput: '45-year-old business consultant who runs an incubator offering office space and mentorship to startups.'"
        template += "\n\nInput: 'A biotech startup focused on gene therapy research.'"
        template += "\nOutput: '38-year-old biotech entrepreneur leading a startup focused on gene therapy research.'"
        
        messages = [
            {
                "role": "system",
                "content": "You are a UX researcher who takes concise, natural notes about individual people. You restate information in a single sentence that sounds like something a human would write in their notebook. You never add prefacing text or explanations. You ONLY write about individual human personas, NEVER companies or organizations. If given information about a business or organization, you ALWAYS convert it to describe a specific person who works at, owns, or runs that business."
            },
            {
                "role": "user",
                "content": template
            }
        ]

        # Add validation and retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": "google/gemini-2.0-flash-001",
                        "messages": messages,
                        "temperature": 0.7  # Moderate temperature for rephrasing
                    }
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"].strip()
                
                # Validate that the response is about a person
                business_indicators = ["this is a business", "this business", "this company", "this organization", 
                                      "we're talking about a business", "a business that", "the business", 
                                      "they offer", "they provide", "they specialize"]
                
                is_about_business = any(indicator.lower() in content.lower() for indicator in business_indicators)
                
                if is_about_business and attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt+1}/{max_retries}: Response still describes a business: {content[:50]}...")
                    # Add more explicit instructions for the retry
                    retry_message = {
                        "role": "user",
                        "content": "Your response still describes a business or organization, not a person. Please convert this to describe a SPECIFIC INDIVIDUAL PERSON who owns, runs, or works at this business. Include their age and personal characteristics. For example: '42-year-old founder of a tech startup who...' or '35-year-old manager at a retail business who...'"
                    }
                    messages.append(retry_message)
                    continue
                
                logger.info(f"Successfully restated persona: {content[:50]}...")
                return content
            except Exception as e:
                logger.error(f"Error restating persona: {str(e)}")
                if attempt == max_retries - 1:
                    # If all retries fail, convert it manually as a last resort
                    if any(business_term in base_persona.lower() for business_term in ["business", "company", "startup", "organization", "firm", "enterprise"]):
                        age = random.randint(35, 55)
                        roles = ["founder", "CEO", "manager", "director", "owner", "entrepreneur"]
                        role = random.choice(roles)
                        return f"{age}-year-old {role} of a {base_persona.lower().strip('.')}"
                    # If it's not clearly a business, return the original
                    return base_persona
        
        # If we get here, all attempts failed
        return base_persona

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
