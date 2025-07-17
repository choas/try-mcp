# Multi-Service MCP Platform Services

This document provides detailed information about each service available in the Multi-Service MCP Platform.

## Table of Contents

1. [MVG Service](#mvg-service)
2. [Mindful Service](#mindful-service)
3. [Weather Service](#weather-service)
4. [Emoji Oracle Service](#emoji-oracle-service)
5. [Timestamp Service](#timestamp-service)
6. [Fortune Cookie Service](#fortune-cookie-service)
7. [Lucky Numbers Service](#lucky-numbers-service)

## MVG Service

The MVG Service provides real-time information about Munich's public transportation system.

### Endpoint

- `/mvg/v1`

### Tools

#### get_departures

Get real-time departures from a Munich public transport station.

**Parameters:**
- `station` (string, required): Name of the station
- `limit` (integer, optional): Maximum number of departures to return
- `offset` (integer, optional): Time offset in minutes

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_departures",
    "arguments": {
      "station": "Hauptbahnhof",
      "limit": 5,
      "offset": 10
    }
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Departures from Hauptbahnhof in 10 minutes:\n\n1. S1 to Ostbahnhof (11:35)\n2. U4 to Arabellapark (11:36)\n3. S8 to Flughafen München (11:38)\n4. U5 to Neuperlach Süd (11:40)\n5. Tram 19 to Berg am Laim (11:42)"
      }
    ],
    "is_error": false
  }
}
```

#### find_station

Find stations by name or partial name.

**Parameters:**
- `query` (string, required): Station name or partial name
- `limit` (integer, optional): Maximum number of results to return

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "find_station",
    "arguments": {
      "query": "Marien",
      "limit": 3
    }
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Stations matching 'Marien':\n\n1. Marienplatz\n2. Marienhof\n3. Mariensäule"
      }
    ],
    "is_error": false
  }
}
```

## Mindful Service

The Mindful Service provides inspirational sentences that rotate throughout the day.

### Endpoint

- `/mindful/v1`

### Tools

#### get_mindful_sentence

Get an inspirational mindful sentence for the day.

**Parameters:** None

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_mindful_sentence",
    "arguments": {}
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Take a moment to breathe deeply and connect with the present moment."
      }
    ],
    "is_error": false
  }
}
```

### Implementation Details

- The service maintains a pool of 50+ inspirational sentences
- Each day, 4 different sentences are selected for rotation
- The same sentence is returned for multiple calls within the same time period
- Sentences reset at midnight for a new day

## Weather Service

The Weather Service provides consistently optimistic weather forecasts.

### Endpoint

- `/weather/v1`

### Tools

#### get_weather_forecast

Get an optimistic weather forecast for tomorrow.

**Parameters:** None

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_weather_forecast",
    "arguments": {}
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Tomorrow will be a beautiful day with a temperature of 22°C (72°F) and partly cloudy skies. Perfect for outdoor activities!"
      }
    ],
    "is_error": false
  }
}
```

### Implementation Details

- Always predicts pleasant weather conditions
- Temperature ranges between 18-24°C (64-75°F)
- Only sunny or partly cloudy conditions
- No rain, storms, or extreme temperatures
- Slight variations in forecasts for variety

## Emoji Oracle Service

The Emoji Oracle Service provides cryptic guidance through emoji combinations.

### Endpoint

- `/emoji-oracle/v1`

### Tools

#### get_emoji_oracle

Get a cryptic three-emoji combination as guidance.

**Parameters:** None

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_emoji_oracle",
    "arguments": {}
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "🌟 🔑 🚪\n\nThe oracle has spoken. Interpret these symbols as guidance for your path."
      }
    ],
    "is_error": false
  }
}
```

### Implementation Details

- Returns exactly 3 emojis per request
- Draws from a diverse pool of meaningful symbols organized by categories
- Creates potentially interpretable but cryptic messages
- Different combinations for each request
- Includes a mystical message to accompany the emojis

## Timestamp Service

The Timestamp Service generates random timestamps within specified ranges.

### Endpoint

- `/timestamp/v1`

### Tools

#### generate_random_timestamp

Generate a random timestamp within a specified range.

**Parameters:**
- `start_time` (string, optional): Start of the time range (ISO 8601 format)
- `end_time` (string, optional): End of the time range (ISO 8601 format)

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "generate_random_timestamp",
    "arguments": {
      "start_time": "2025-01-01T00:00:00Z",
      "end_time": "2025-12-31T23:59:59Z"
    }
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "2025-07-15T14:23:47Z"
      }
    ],
    "is_error": false
  }
}
```

### Implementation Details

- Generates random timestamps within specified ranges
- Automatically swaps start/end times if start is after end
- Default range is next day between 10:00 and 16:00
- Returns timestamps in ISO 8601 format
- Validates input parameters for proper date formats

## Fortune Cookie Service

The Fortune Cookie Service provides surreal and cryptic phrases that change hourly.

### Endpoint

- `/fortune/v1`

### Tools

#### get_fortune_cookie

Get a surreal, cryptic fortune phrase.

**Parameters:** None

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_fortune_cookie",
    "arguments": {}
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "The silent whisper of forgotten dreams echoes in the corridors of possibility."
      }
    ],
    "is_error": false
  }
}
```

### Implementation Details

- Generates surreal, cryptic phrases
- Same phrase returned within the same hour
- New phrase generated each hour
- LLM integration for content generation
- Supports MCP prompts/list method
- Caching mechanism to ensure consistent responses within the same hour

### Prompts Support

This service also supports the MCP `prompts/list` method, which returns a list of prompts that can be used to generate fortune cookie phrases.

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "prompts/list",
  "params": {}
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "prompts": [
      {
        "name": "surreal_fortune",
        "description": "Generate a surreal, cryptic fortune cookie phrase",
        "inputSchema": {
          "type": "object",
          "properties": {},
          "required": []
        }
      }
    ]
  }
}
```

## Lucky Numbers Service

The Lucky Numbers Service generates "statistically blessed" numbers for various life scenarios.

### Endpoint

- `/lucky-numbers/v1`

### Tools

#### generate_blessed_numbers

Generates mystically optimized numbers for various life scenarios.

**Parameters:**
- `scenario` (string, required): The scenario for which you need lucky numbers
  - Options: lottery, decision, restaurant, date, love, career, creativity, health, travel, learning
- `count` (integer, optional): Number of lucky numbers to generate (1-10)
- `min_value` (integer, optional): Minimum value for generated numbers
- `max_value` (integer, optional): Maximum value for generated numbers
- `energy_level` (string, optional): Intensity of cosmic energy applied
  - Options: low, medium, high, extreme

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "generate_blessed_numbers",
    "arguments": {
      "scenario": "lottery",
      "count": 6,
      "min_value": 1,
      "max_value": 49,
      "energy_level": "high"
    }
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "🎯 🍀 💰\n\n✨ LUCKY NUMBERS FOR LOTTERY ✨\n\nYour blessed numbers: 7, 13, 23, 28, 36, 42\n\nScenario: Numbers for lottery games and jackpots\nCosmic Alignment: 92%\nMystical Methodology: Quantum Fluctuation Analysis\nEnergy Level: Powerful mystical forces with strong manifestation potential\n\nThe cosmic forces are strongly aligned in your favor today!"
      }
    ],
    "is_error": false
  }
}
```

### Implementation Details

- Scenario-specific number generation for 10 different contexts
- Mystical methodology explanations and cosmic alignment calculation
- Customizable parameters (count, range, energy level)
- Formatted responses with emojis and encouraging language
- Consistent but varied results based on energy level and scenario

### Available Scenarios

1. **lottery**: Numbers for lottery games and jackpots
2. **decision**: A single number to help make binary decisions
3. **restaurant**: Numbers for selecting a restaurant from your list
4. **date**: Lucky day of the month for planning important events
5. **love**: Numbers to enhance romantic decisions and timing
6. **career**: Numbers to guide professional decisions
7. **creativity**: Numbers to inspire creative projects and ideas
8. **health**: Numbers for wellness routines and health decisions
9. **travel**: Numbers for trip planning and destination selection
10. **learning**: Numbers to guide educational choices and study timing

### Energy Levels

1. **low**: Subtle cosmic influence with gentle guidance
2. **medium**: Balanced energetic flow with moderate cosmic alignment
3. **high**: Powerful mystical forces with strong manifestation potential
4. **extreme**: Extraordinary cosmic convergence with maximum blessing potential