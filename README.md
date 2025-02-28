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
- Uses local persona database with fallback options

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

The service is available at `https://gen.kolidos.com` and exposes the following endpoints:

### Generate a UX Persona

**Endpoint:** `POST https://gen.kolidos.com/generate`

**Headers:**
```
Content-Type: application/json
X-API-Key: your_api_secret_key
```

**Request Body:**
```json
{
    "base_persona": "Your persona description here"
}
```

**Example Request:**
```bash
curl -X POST "https://gen.kolidos.com/generate" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_secret_key" \
     -d '{"base_persona": "A 28-year-old software engineer who loves building side projects."}'
```

### Get a Random Persona

**Endpoint:** `GET https://gen.kolidos.com/random-persona`

**Headers:**
```
X-API-Key: your_api_secret_key
```

**Example Request:**
```bash
curl -X GET "https://gen.kolidos.com/random-persona" \
     -H "X-API-Key: your_api_secret_key"
```

### Get a Random UX Persona (Combined Endpoint)

**Endpoint:** `GET https://gen.kolidos.com/random-ux-persona`

**Headers:**
```
X-API-Key: your_api_secret_key
```

**Example Request:**
```bash
curl -X GET "https://gen.kolidos.com/random-ux-persona" \
     -H "X-API-Key: your_api_secret_key"
```

### Get a Random Name

**Endpoint:** `GET https://gen.kolidos.com/random-name`

**Headers:**
```
X-API-Key: your_api_secret_key
```

**Example Request:**
```bash
curl -X GET "https://gen.kolidos.com/random-name" \
     -H "X-API-Key: your_api_secret_key"
```

**Example Response:**
```json
{
    "name": "Sarah Jane Wilson",
    "base_persona": "A 35-year-old marketing manager who struggles with work-life balance."
}
```

### Expand a Name into a Full Persona

**Endpoint:** `POST https://gen.kolidos.com/expand-persona`

**Headers:**
```
Content-Type: application/json
X-API-Key: your_api_secret_key
```

**Request Body:**
```json
{
    "name": "Sarah Jane Wilson",
    "title": "Digital Nomad",
    "description": "A 35-year-old marketing manager who struggles with work-life balance"
}
```

> **Note:** The `title` and `description` fields are optional. If provided, they will be incorporated into the generated persona. If omitted, the API will generate a persona based solely on the name.

**Example Request:**
```bash
curl -X POST "https://gen.kolidos.com/expand-persona" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_secret_key" \
     -d '{"name": "Sarah Jane Wilson", "title": "Digital Nomad", "description": "A 35-year-old marketing manager who struggles with work-life balance"}'
```

### Check API Health

**Endpoint:** `GET https://gen.kolidos.com/health`

**Example Request:**
```bash
curl -X GET "https://gen.kolidos.com/health"
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
  -H "X-API-Key: your_api_secret_key" \
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
        json={"base_persona": base_persona},
        headers={"X-API-Key": "your_api_secret_key"}
    )
    return response.json()
```

**JavaScript:**
```javascript
async function generatePersona(basePersona) {
    const response = await fetch('http://localhost:9350/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'your_api_secret_key'
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
        json={"base_persona": base_persona},
        headers={"X-API-Key": "your_api_secret_key"}
    )
    response.raise_for_status()
    persona = response.json()
except requests.exceptions.RequestException as e:
    print(f"Error generating persona: {e}")
```

## Security Considerations

This API implements multiple layers of security that can be used depending on your deployment scenario:

### 1. API Key Authentication (Built-in)

The service requires an API key for all requests to the `/generate` endpoint. This key is defined in your environment variables:

```
API_SECRET_KEY=your_secret_key_here
```

To generate a secure random API key, use this command:

```bash
openssl rand -hex 32
# Example output: d7342c173c86ec331b94e5f28b600412a992a9addd3a2a0fc3efcc87450871a1
```

All requests must include this key in the `X-API-Key` header:

```bash
curl -X POST http://localhost:9350/generate \
  -H "X-API-Key: your_secret_key_here" \
  -H "Content-Type: application/json" \
  -d '{"base_persona": "..."}'
```

### 2. Network Security Options

Depending on your deployment scenario, consider these additional security layers:

#### For Internal Networks

- **Docker Network Isolation**: When deploying with other containers, use Docker's network isolation to limit access to only the containers that need it.
- **Reverse Proxy**: Place the service behind a reverse proxy like Nginx or Traefik to add TLS and additional authentication.
- **Firewall Rules**: Configure firewall rules on your host to restrict access to the service's port.

#### For Public Access

- **Cloudflare Tunnel + Access**: As described in the Deployment section, use Cloudflare Tunnel with Access policies to restrict by IP address.
- **VPN**: Require VPN access to your network before the service can be reached.
- **TLS**: Always use HTTPS for any publicly accessible endpoint.

### 3. Monitoring and Rate Limiting

- Monitor API usage for unusual patterns
- Consider implementing rate limiting for production deployments
- Regularly rotate your API keys

### Security Recommendations

1. **Never expose the service directly to the internet without authentication**
2. **Use a strong, randomly generated API key**
3. **Rotate your API keys periodically**
4. **Monitor logs for unauthorized access attempts**

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

## JSON Response Structure

The `/generate`, `/random-ux-persona`, and `/expand-persona` endpoints return a JSON object with the following structure:

```