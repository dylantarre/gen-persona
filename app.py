from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from persona_generator import PersonaGenerator
import uvicorn
import os
import random
from dotenv import load_dotenv
import logging

load_dotenv()

app = FastAPI(title="Persona Generator API")
generator = PersonaGenerator()

# Load personas at startup
personas = generator.load_personas()
if not personas:
    raise Exception("Failed to load PersonaHub personas")

# After loading personas
logging.info(f"Loaded {len(personas) if personas else 0} personas")

# Get API key from environment variable
API_KEY = os.getenv("API_SECRET_KEY", "default-dev-key-change-me")

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

class PersonaRequest(BaseModel):
    base_persona: str

class PersonaResponse(BaseModel):
    ux_persona: str

class RandomPersonaResponse(BaseModel):
    base_persona: str

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
            raise HTTPException(status_code=500, detail="No personas available")
        random_persona = random.choice(personas)
        return {"base_persona": random_persona}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/version")
async def version():
    return {"version": "2.0", "updated": True}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9350, reload=True)
