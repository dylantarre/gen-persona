from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from persona_generator import PersonaGenerator
import uvicorn
import ipaddress

app = FastAPI(title="Persona Generator API")
generator = PersonaGenerator()

# List of allowed IP addresses
ALLOWED_IPS = [
    "203.0.113.1",  # Example IP 1
    "203.0.113.2",  # Example IP 2
    "192.168.1.0/24",  # Example CIDR range
]

def verify_ip_middleware(request: Request):
    client_ip = request.client.host
    
    # Check if the client IP is in the allowed list
    if not any(client_ip == ip or (
        "/" in ip and ipaddress.ip_address(client_ip) in ipaddress.ip_network(ip)
    ) for ip in ALLOWED_IPS):
        raise HTTPException(status_code=403, detail="Access denied")
    return client_ip

class PersonaRequest(BaseModel):
    base_persona: str

class PersonaResponse(BaseModel):
    ux_persona: str

@app.post("/generate", response_model=PersonaResponse)
async def generate_persona(request: PersonaRequest, client_ip: str = Depends(verify_ip_middleware)):
    try:
        ux_persona = generator.generate_ux_persona(request.base_persona)
        if not ux_persona:
            raise HTTPException(status_code=500, detail="Failed to generate UX persona")
        return PersonaResponse(ux_persona=ux_persona)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check(client_ip: str = Depends(verify_ip_middleware)):
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9350)
