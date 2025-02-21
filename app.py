from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from persona_generator import PersonaGenerator
import uvicorn

app = FastAPI(title="Persona Generator API")
generator = PersonaGenerator()

class PersonaRequest(BaseModel):
    base_persona: str

class PersonaResponse(BaseModel):
    ux_persona: str

@app.post("/generate", response_model=PersonaResponse)
async def generate_persona(request: PersonaRequest):
    try:
        ux_persona = generator.generate_ux_persona(request.base_persona)
        if not ux_persona:
            raise HTTPException(status_code=500, detail="Failed to generate UX persona")
        return PersonaResponse(ux_persona=ux_persona)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9350, reload=True)
