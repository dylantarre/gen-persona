# Persona Generator

A powerful API service that generates detailed UX personas using Google's Gemini 2.0 Flash model through OpenRouter. This tool helps UX researchers, product managers, and designers create comprehensive user personas for their projects.

## Features

- Uses Gemini 2.0 Flash through OpenRouter for high-quality persona generation
- Generates detailed UX personas with:
  - Demographics
  - Goals
  - Frustrations
  - Behaviors
  - Motivations
  - Technological proficiency
  - Preferred communication channels
- Runs as a containerized service
- Easy deployment with Docker and Portainer
- RESTful API interface

## Installation

### Using Docker Hub

The easiest way to get started is to pull the pre-built Docker image from Docker Hub:

```bash
docker pull dylantarre/gen-persona:latest
```

Then run it with:

```bash
docker run -p 9350:9350 -e OPENROUTER_API_KEY=your_api_key dylantarre/gen-persona:latest
```

### Using Docker Compose

1. Make sure you have Docker and Docker Compose installed

2. Create and configure your `.env` file as described above

3. Build and run the container:
```bash
docker-compose up -d
```

### Portainer Deployment

1. In Portainer, go to "Stacks" and click "Add stack"
2. Upload the `docker-compose.yml` file or paste its contents
3. Add your environment variables:
   - `OPENROUTER_API_KEY`: Your OpenRouter API key
4. Deploy the stack

## API Usage

The service runs on port 9350 and exposes two endpoints:

### Generate Persona

**Endpoint:** `POST http://localhost:9350/generate`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "base_persona": "Your persona description here"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:9350/generate \
  -H "Content-Type: application/json" \
  -d '{
    "base_persona": "A 28-year-old software engineer who loves rock climbing and building side projects in their spare time. They are passionate about clean code and sustainable development practices."
  }'
```

### Health Check

**Endpoint:** `GET http://localhost:9350/health`

**Example:**
```bash
curl http://localhost:9350/health
```

## Deployment with Cloudflare Tunnel

To deploy this service securely with IP-based access restrictions using Cloudflare Tunnel:

### 1. Set Up Cloudflare Tunnel

1. Install `cloudflared` on your server:
   ```bash
   # On Ubuntu/Debian
   curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared.deb
   
   # On macOS
   brew install cloudflare/cloudflare/cloudflared
   ```

2. Authenticate with Cloudflare:
   ```bash
   cloudflared tunnel login
   ```

3. Create a tunnel:
   ```bash
   cloudflared tunnel create gen-persona
   ```

4. Configure the tunnel by creating a config file at `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: <TUNNEL_ID>
   credentials-file: /path/to/.cloudflared/<TUNNEL_ID>.json
   
   ingress:
     - hostname: gen-persona.lg.media
       service: http://localhost:9350
     - service: http_status:404
   ```

5. Create a DNS record for your domain:
   ```bash
   cloudflared tunnel route dns <TUNNEL_ID> gen-persona.lg.media
   ```

6. Start the tunnel:
   ```bash
   cloudflared tunnel run
   ```

### 2. IP Restriction with Cloudflare Access

1. Go to the Cloudflare Zero Trust dashboard
2. Navigate to Access → Applications
3. Create a new application for `gen-persona.lg.media`
4. Create an Access policy with an "Allow" rule using the "IP Address" selector
5. Add your allowed IP addresses or CIDR ranges

### 3. Making API Requests

When using Cloudflare Access, include the CF Access token in your requests:

```bash
curl -X POST https://gen-persona.lg.media/generate \
  -H "CF-Access-Client-Id: YOUR_ACCESS_CLIENT_ID" \
  -H "CF-Access-Client-Secret: YOUR_ACCESS_CLIENT_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"base_persona": "A 28-year-old software engineer who loves rock climbing"}'
```

## Best Practices for Using the Service

### Writing Effective Base Personas

1. **Be Specific**: Include key demographic information, interests, and behaviors
   ```json
   {
     "base_persona": "A 35-year-old marketing manager in Toronto with two kids. They work remotely, are tech-savvy, and struggle with work-life balance."
   }
   ```

2. **Include Context**: Add relevant professional or personal context
   ```json
   {
     "base_persona": "A freelance graphic designer transitioning from print to digital design. They have 10 years of experience but feel overwhelmed by new design tools."
   }
   ```

3. **Add Pain Points**: Mention challenges or frustrations
   ```json
   {
     "base_persona": "A small business owner who finds digital marketing confusing. They want to grow their online presence but have limited time and budget."
   }
   ```

### Integration Examples

**Python:**
```python
import requests

def generate_persona(base_persona):
    response = requests.post(
        "http://localhost:9350/generate",
        json={"base_persona": base_persona}
    )
    return response.json()
```

**JavaScript:**
```javascript
async function generatePersona(basePersona) {
    const response = await fetch('http://localhost:9350/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ base_persona: basePersona })
    });
    return await response.json();
}
```

### Error Handling

The API returns standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid input)
- 500: Internal Server Error

Always implement proper error handling in your applications:

```python
try:
    response = requests.post(
        "http://localhost:9350/generate",
        json={"base_persona": base_persona}
    )
    response.raise_for_status()
    persona = response.json()
except requests.exceptions.RequestException as e:
    print(f"Error generating persona: {e}")
```

## Monitoring

The service includes a health check endpoint that can be used for monitoring:

```bash
# Using curl
curl http://localhost:9350/health

# Using wget
wget -qO- http://localhost:9350/health
```

Docker Compose is configured to perform automatic health checks every 30 seconds.

## Rate Limiting

Be mindful of OpenRouter's rate limits. Consider implementing your own rate limiting if you're making multiple requests:

```python
import time

def generate_multiple_personas(base_personas, delay_seconds=1):
    results = []
    for persona in base_personas:
        result = generate_persona(persona)
        results.append(result)
        time.sleep(delay_seconds)  # Rate limiting
    return results
```

## Support

For issues and feature requests, please open an issue in the repository.
