from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from persona_generator import PersonaGenerator
import uvicorn
import os
import random
from dotenv import load_dotenv
import logging
from typing import Optional

load_dotenv()

app = FastAPI(title="Persona Generator API")
generator = PersonaGenerator()

# Load personas at startup
personas = generator.load_personas()
if personas:
    logging.info(f"Loaded {len(personas)} personas")
    if len(personas) <= 5:
        logging.warning("Using fallback personas since local file could not be loaded")
else:
    logging.warning("No personas were loaded, random-persona endpoint will not be available")
    personas = []

# Get API key from environment variable
API_KEY = os.getenv("API_SECRET_KEY", "default-dev-key-change-me")

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

class PersonaRequest(BaseModel):
    base_persona: str

class PersonaResponse(BaseModel):
    ux_persona: str  # This will now contain a JSON string

class RandomPersonaResponse(BaseModel):
    base_persona: str

class NameResponse(BaseModel):
    name: str
    title: str
    base_persona: str

class ExpandPersonaRequest(BaseModel):
    name: str
    title: Optional[str] = None
    description: Optional[str] = None

class NameRequest(BaseModel):
    base_persona: str
    restate: Optional[bool] = False

@app.post("/generate", response_model=PersonaResponse)
async def generate_persona(request: PersonaRequest, api_key: str = Depends(verify_api_key)):
    try:
        ux_persona = generator.generate_ux_persona(request.base_persona)
        if not ux_persona:
            raise HTTPException(status_code=500, detail="Failed to generate persona")
        return {"ux_persona": ux_persona}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/random-persona", response_model=RandomPersonaResponse)
async def get_random_persona(api_key: str = Depends(verify_api_key)):
    try:
        if not personas or len(personas) == 0:
            raise HTTPException(status_code=503, detail="No personas available. The PersonaHub dataset could not be loaded.")
        random_persona = random.choice(personas)
        return {"base_persona": random_persona}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/random-ux-persona", response_model=PersonaResponse)
async def get_random_ux_persona(api_key: str = Depends(verify_api_key)):
    try:
        if not personas or len(personas) == 0:
            raise HTTPException(status_code=503, detail="No personas available. The persona dataset could not be loaded.")
        
        # Get a random base persona
        random_persona = random.choice(personas)
        logging.info(f"Selected random persona: {random_persona[:50]}...")
        
        # Generate UX persona from the random base persona
        ux_persona = generator.generate_ux_persona(random_persona)
        if not ux_persona:
            raise HTTPException(status_code=500, detail="Failed to generate UX persona")
        
        return {"ux_persona": ux_persona}
    except Exception as e:
        logging.error(f"Error generating random UX persona: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/random-name", response_model=NameResponse)
async def get_random_name(api_key: str = Depends(verify_api_key)):
    """Generate a random name based on a random base persona"""
    try:
        if not personas or len(personas) == 0:
            raise HTTPException(status_code=503, detail="No personas available")
        
        random_persona = random.choice(personas)
        name_response = generator.generate_name(random_persona, restate=False)
        
        if not name_response or 'name' not in name_response:
            raise HTTPException(status_code=500, detail="Failed to generate name")
            
        return name_response
    except Exception as e:
        logging.error(f"Error generating random name: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/name-with-restate", response_model=NameResponse)
async def get_name_with_restate(api_key: str = Depends(verify_api_key)):
    """Generate a random name based on a random base persona with restatement"""
    try:
        if not personas or len(personas) == 0:
            raise HTTPException(status_code=503, detail="No personas available")
        
        random_persona = random.choice(personas)
        name_response = generator.generate_name(random_persona, restate=True)
        
        if not name_response or 'name' not in name_response:
            raise HTTPException(status_code=500, detail="Failed to generate name")
            
        return name_response
    except Exception as e:
        logging.error(f"Error generating name with restate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/expand-persona", response_model=PersonaResponse)
async def expand_persona(request: ExpandPersonaRequest, api_key: str = Depends(verify_api_key)):
    """Expand a name into a full UX persona"""
    try:
        if not request.name:
            raise HTTPException(status_code=400, detail="Name is required")
        
        # Create a base persona from the name
        base_persona_parts = [f"A person named {request.name}"]
        if request.title:
            base_persona_parts.append(f" with title {request.title}")
        if request.description:
            base_persona_parts.append(f" who is described as {request.description}")
        base_persona = " ".join(base_persona_parts)
        
        # Generate full UX persona
        ux_persona = generator.generate_ux_persona(base_persona)
        if not ux_persona:
            raise HTTPException(status_code=500, detail="Failed to generate persona")
        
        return {"ux_persona": ux_persona}
    except Exception as e:
        logging.error(f"Error expanding persona: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-name", response_model=NameResponse)
async def generate_name(request: NameRequest, api_key: str = Depends(verify_api_key)):
    """Generate a name based on a provided persona with optional restatement"""
    try:
        if not request.base_persona:
            raise HTTPException(status_code=400, detail="Base persona is required")
        
        name_response = generator.generate_name(request.base_persona, restate=request.restate)
        
        if not name_response or 'name' not in name_response:
            raise HTTPException(status_code=500, detail="Failed to generate name")
            
        return name_response
    except Exception as e:
        logging.error(f"Error generating name: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/version")
async def version():
    return {"version": "2.0", "updated": True}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9350, reload=True)
