# Multi-Service MCP Platform Usage Examples

This document provides detailed examples of how to use the Multi-Service MCP Platform with various programming languages and tools.

## Table of Contents

1. [Using cURL](#using-curl)
2. [Using Python](#using-python)
3. [Using JavaScript](#using-javascript)
4. [Using Claude Desktop](#using-claude-desktop)
5. [Direct API Calls](#direct-api-calls)

## Using cURL

### List All Available Tools

```bash
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}'
```

### Initialize Connection

```bash
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}'
```

### MVG Service: Get Departures

```bash
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "mvg_get_departures",
    "arguments": {
      "station": "Hauptbahnhof",
      "limit": 5
    }
  }
}'
```

### Mindful Service: Get Mindful Sentence

```bash
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "mindful_get_mindful_sentence",
    "arguments": {}
  }
}'
```

### Weather Service: Get Weather Forecast

```bash
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "weather_get_weather_forecast",
    "arguments": {}
  }
}'
```

### Emoji Oracle Service: Get Emoji Oracle

```bash
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "emoji-oracle_get_emoji_oracle",
    "arguments": {}
  }
}'
```

### Timestamp Service: Generate Random Timestamp

```bash
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "timestamp_generate_random_timestamp",
    "arguments": {
      "start_time": "2025-01-01T00:00:00Z",
      "end_time": "2025-12-31T23:59:59Z"
    }
  }
}'
```

### Fortune Cookie Service: Get Fortune Cookie

```bash
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "fortune_get_fortune_cookie",
    "arguments": {}
  }
}'
```

### Lucky Numbers Service: Generate Blessed Numbers

```bash
curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "lucky-numbers_generate_blessed_numbers",
    "arguments": {
      "scenario": "lottery",
      "count": 6,
      "energy_level": "high"
    }
  }
}'
```

### Using Service-Specific Endpoints

```bash
# List tools for a specific service
curl -X POST http://localhost:8003/services/lucky-numbers/v1 -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}'

# Call a specific tool on a service
curl -X POST http://localhost:8003/services/lucky-numbers/v1 -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "generate_blessed_numbers",
    "arguments": {
      "scenario": "lottery",
      "count": 6
    }
  }
}'
```

### Using Direct Method Calls

```bash
# Call a method directly
curl -X POST http://localhost:8003/services/mvg/v1/get_departures -H "Content-Type: application/json" -d '{
  "station": "Hauptbahnhof"
}'

# Get a mindful sentence
curl -X POST http://localhost:8003/services/mindful/v1/get_mindful_sentence
```

## Using Python

### Basic MCP Client

```python
import requests
import json

class MCPClient:
    def __init__(self, base_url="http://localhost:8003"):
        self.base_url = base_url
        self.mcp_endpoint = f"{base_url}/mcp"
        self.request_id = 1
    
    def initialize(self):
        response = self._send_request("initialize", {})
        return response
    
    def list_tools(self):
        response = self._send_request("tools/list", {})
        return response.get("result", {}).get("tools", [])
    
    def call_tool(self, tool_name, arguments=None):
        if arguments is None:
            arguments = {}
        
        response = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        return response.get("result", {})
    
    def _send_request(self, method, params):
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        self.request_id += 1
        
        response = requests.post(
            self.mcp_endpoint,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        return response.json()

# Usage examples
client = MCPClient()

# Initialize connection
init_response = client.initialize()
print("Initialized:", init_response)

# List available tools
tools = client.list_tools()
print(f"Available tools: {len(tools)}")
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")

# Get a mindful sentence
mindful_response = client.call_tool("mindful_get_mindful_sentence")
print("\nMindful sentence:")
for content in mindful_response.get("content", []):
    if content["type"] == "text":
        print(content["text"])

# Get lucky numbers for lottery
lucky_response = client.call_tool("lucky-numbers_generate_blessed_numbers", {
    "scenario": "lottery",
    "count": 6,
    "energy_level": "high"
})
print("\nLucky numbers:")
for content in lucky_response.get("content", []):
    if content["type"] == "text":
        print(content["text"])
```

### Service-Specific Client

```python
import requests
import json

class ServiceClient:
    def __init__(self, service_name, version="v1", base_url="http://localhost:8003"):
        self.base_url = base_url
        self.service_name = service_name
        self.version = version
        self.endpoint = f"{base_url}/services/{service_name}/{version}"
        self.request_id = 1
    
    def list_tools(self):
        response = self._send_request("tools/list", {})
        return response.get("result", {}).get("tools", [])
    
    def call_tool(self, tool_name, arguments=None):
        if arguments is None:
            arguments = {}
        
        response = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        return response.get("result", {})
    
    def call_direct(self, method_name, params=None):
        if params is None:
            params = {}
        
        response = requests.post(
            f"{self.endpoint}/{method_name}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(params)
        )
        
        return response.json()
    
    def _send_request(self, method, params):
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        self.request_id += 1
        
        response = requests.post(
            self.endpoint,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        return response.json()

# Usage examples
lucky_client = ServiceClient("lucky-numbers")

# List tools for the service
tools = lucky_client.list_tools()
print(f"Lucky Numbers Service Tools: {len(tools)}")
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")

# Generate lucky numbers
response = lucky_client.call_tool("generate_blessed_numbers", {
    "scenario": "lottery",
    "count": 6,
    "energy_level": "high"
})
print("\nLucky numbers response:")
for content in response.get("content", []):
    if content["type"] == "text":
        print(content["text"])

# Direct method call
direct_response = lucky_client.call_direct("generate_blessed_numbers", {
    "scenario": "career",
    "count": 2
})
print("\nDirect method response:")
print(direct_response)
```

## Using JavaScript

### Basic MCP Client

```javascript
class MCPClient {
  constructor(baseUrl = 'http://localhost:8003') {
    this.baseUrl = baseUrl;
    this.mcpEndpoint = `${baseUrl}/mcp`;
    this.requestId = 1;
  }

  async initialize() {
    const response = await this._sendRequest('initialize', {});
    return response;
  }

  async listTools() {
    const response = await this._sendRequest('tools/list', {});
    return response?.result?.tools || [];
  }

  async callTool(toolName, arguments = {}) {
    const response = await this._sendRequest('tools/call', {
      name: toolName,
      arguments: arguments
    });
    
    return response?.result;
  }

  async _sendRequest(method, params) {
    const payload = {
      jsonrpc: '2.0',
      id: this.requestId++,
      method: method,
      params: params
    };

    const response = await fetch(this.mcpEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    return await response.json();
  }
}

// Usage example
async function main() {
  const client = new MCPClient();
  
  // Initialize connection
  const initResponse = await client.initialize();
  console.log('Initialized:', initResponse);
  
  // List available tools
  const tools = await client.listTools();
  console.log(`Available tools: ${tools.length}`);
  tools.forEach(tool => {
    console.log(`- ${tool.name}: ${tool.description}`);
  });
  
  // Get a mindful sentence
  const mindfulResponse = await client.callTool('mindful_get_mindful_sentence');
  console.log('\nMindful sentence:');
  mindfulResponse?.content?.forEach(content => {
    if (content.type === 'text') {
      console.log(content.text);
    }
  });
  
  // Get lucky numbers for lottery
  const luckyResponse = await client.callTool('lucky-numbers_generate_blessed_numbers', {
    scenario: 'lottery',
    count: 6,
    energy_level: 'high'
  });
  console.log('\nLucky numbers:');
  luckyResponse?.content?.forEach(content => {
    if (content.type === 'text') {
      console.log(content.text);
    }
  });
}

main().catch(console.error);
```

### Service-Specific Client

```javascript
class ServiceClient {
  constructor(serviceName, version = 'v1', baseUrl = 'http://localhost:8003') {
    this.baseUrl = baseUrl;
    this.serviceName = serviceName;
    this.version = version;
    this.endpoint = `${baseUrl}/services/${serviceName}/${version}`;
    this.requestId = 1;
  }

  async listTools() {
    const response = await this._sendRequest('tools/list', {});
    return response?.result?.tools || [];
  }

  async callTool(toolName, arguments = {}) {
    const response = await this._sendRequest('tools/call', {
      name: toolName,
      arguments: arguments
    });
    
    return response?.result;
  }

  async callDirect(methodName, params = {}) {
    const response = await fetch(`${this.endpoint}/${methodName}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params)
    });

    return await response.json();
  }

  async _sendRequest(method, params) {
    const payload = {
      jsonrpc: '2.0',
      id: this.requestId++,
      method: method,
      params: params
    };

    const response = await fetch(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    return await response.json();
  }
}

// Usage example
async function main() {
  const luckyClient = new ServiceClient('lucky-numbers');
  
  // List tools for the service
  const tools = await luckyClient.listTools();
  console.log(`Lucky Numbers Service Tools: ${tools.length}`);
  tools.forEach(tool => {
    console.log(`- ${tool.name}: ${tool.description}`);
  });
  
  // Generate lucky numbers
  const response = await luckyClient.callTool('generate_blessed_numbers', {
    scenario: 'lottery',
    count: 6,
    energy_level: 'high'
  });
  console.log('\nLucky numbers response:');
  response?.content?.forEach(content => {
    if (content.type === 'text') {
      console.log(content.text);
    }
  });
  
  // Direct method call
  const directResponse = await luckyClient.callDirect('generate_blessed_numbers', {
    scenario: 'career',
    count: 2
  });
  console.log('\nDirect method response:');
  console.log(directResponse);
}

main().catch(console.error);
```

## Using Claude Desktop

To use the Multi-Service MCP Platform with Claude Desktop, you need to add the server configuration to your Claude Desktop configuration file.

### Configuration

Add this to your Claude Desktop configuration file (typically `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "multi-service-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/multi-service-mcp-project",
        "python",
        "multi_service_server.py"
      ]
    }
  }
}
```

Replace `/path/to/your/multi-service-mcp-project` with the actual path to your project directory.

### Example Prompts for Claude

Once configured, you can ask Claude to use various services:

#### MVG Service

- "Check departures from Hauptbahnhof"
- "What trains are leaving from Marienplatz?"
- "Show me departures from Sendlinger Tor in 10 minutes"

#### Mindful Service

- "Show me a mindful sentence for today"
- "I need some inspiration"
- "Give me a mindful thought"

#### Weather Service

- "What's the weather forecast for tomorrow?"
- "Will it be nice weather tomorrow?"
- "Should I plan outdoor activities for tomorrow?"

#### Emoji Oracle Service

- "What does the emoji oracle say about my day?"
- "Give me an emoji reading"
- "I need guidance from the emoji oracle"

#### Timestamp Service

- "Generate a random timestamp for next year"
- "I need a random date between January and June 2025"
- "Give me a random timestamp for scheduling"

#### Fortune Cookie Service

- "What's my fortune today?"
- "Give me a fortune cookie"
- "Show me a cryptic fortune"

#### Lucky Numbers Service

- "Generate lucky numbers for the lottery"
- "What are my lucky numbers for making a career decision?"
- "I need blessed numbers for choosing a restaurant from my list of 10 options"
- "Generate high-energy lucky numbers for creative inspiration"

## Direct API Calls

### List All Services

```
GET http://localhost:8003/services
```

Response:
```json
{
  "services": [
    {
      "name": "mvg",
      "version": "v1",
      "description": "Munich public transport departures and station information",
      "status": "active",
      "tools": [
        {
          "name": "get_departures",
          "description": "Get real-time departures from a Munich public transport station",
          "inputSchema": {
            "type": "object",
            "properties": {
              "station": {
                "type": "string",
                "description": "Name of the station"
              },
              "limit": {
                "type": "integer",
                "description": "Maximum number of departures to return"
              },
              "offset": {
                "type": "integer",
                "description": "Time offset in minutes"
              }
            },
            "required": ["station"]
          }
        },
        {
          "name": "find_station",
          "description": "Find stations by name or partial name",
          "inputSchema": {
            "type": "object",
            "properties": {
              "query": {
                "type": "string",
                "description": "Station name or partial name"
              },
              "limit": {
                "type": "integer",
                "description": "Maximum number of results to return"
              }
            },
            "required": ["query"]
          }
        }
      ]
    },
    // Other services...
  ],
  "total_services": 7
}
```

### Get Service Information

```
GET http://localhost:8003/services/lucky-numbers
```

Response:
```json
{
  "name": "lucky-numbers",
  "version": "v1",
  "description": "Generates statistically blessed numbers for various life scenarios",
  "status": "active",
  "tools": [
    {
      "name": "generate_blessed_numbers",
      "description": "Generates mystically optimized numbers for various life scenarios",
      "inputSchema": {
        "type": "object",
        "properties": {
          "scenario": {
            "type": "string",
            "description": "The scenario for which you need lucky numbers",
            "enum": ["lottery", "decision", "restaurant", "date", "love", "career", "creativity", "health", "travel", "learning"]
          },
          "count": {
            "type": "integer",
            "description": "Number of lucky numbers to generate (optional)",
            "minimum": 1,
            "maximum": 10
          },
          "min_value": {
            "type": "integer",
            "description": "Minimum value for generated numbers (optional)"
          },
          "max_value": {
            "type": "integer",
            "description": "Maximum value for generated numbers (optional)"
          },
          "energy_level": {
            "type": "string",
            "description": "Intensity of cosmic energy applied to number generation",
            "enum": ["low", "medium", "high", "extreme"],
            "default": "medium"
          }
        },
        "required": ["scenario"]
      }
    }
  ],
  "available_versions": ["v1"]
}
```

### Health Check

```
GET http://localhost:8003/health
```

Response:
```json
{
  "status": "healthy",
  "platform": "multi-service-mcp",
  "services": {
    "mvg_v1": "active",
    "mindful_v1": "active",
    "weather_v1": "active",
    "emoji-oracle_v1": "active",
    "timestamp_v1": "active",
    "fortune_v1": "active",
    "lucky-numbers_v1": "active"
  },
  "total_services": 7
}
```

### API Information

```
GET http://localhost:8003/api
```

Response:
```json
{
  "service": "Multi-Service MCP Platform",
  "version": "1.0.0",
  "description": "Multi-service MCP platform with routing support",
  "registered_services": [
    {
      "name": "mvg",
      "version": "v1",
      "description": "Munich public transport departures and station information",
      "status": "active"
    },
    // Other services...
  ],
  "endpoints": {
    "services": "/services - List all services",
    "service_info": "/services/{service_name} - Get service information",
    "individual_mcp": "/services/{service_name}/v{version} - Individual MCP endpoint per service",
    "direct_call": "/services/{service_name}/v{version}/{method} - Direct service method call"
  },
  "capabilities": {
    "multi_service": true,
    "service_routing": true,
    "cors": true
  }
}
```

### Enable/Disable Services

```
POST http://localhost:8003/services/mindful/enable
```

Response:
```json
{
  "status": "success",
  "message": "Service 'mindful' enabled"
}
```

```
POST http://localhost:8003/services/mindful/disable
```

Response:
```json
{
  "status": "success",
  "message": "Service 'mindful' disabled"
}
```