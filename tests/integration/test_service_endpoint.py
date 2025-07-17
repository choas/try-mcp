#!/usr/bin/env python3

import asyncio
import json
import pytest
import aiohttp

@pytest.mark.asyncio
async def test_service_endpoint():
    print('=== Testing Service-Specific Endpoint ===')
    
    # Create the request payload
    payload = {
        'jsonrpc': '2.0',
        'id': 12,
        'method': 'prompts/list',
        'params': {}
    }
    
    print('\nSending request to http://localhost:8003/services/fortune/v1...')
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8003/services/fortune/v1', json=payload) as response:
                print(f'Response status: {response.status}')
                if response.status == 200:
                    result = await response.json()
                    print(f'Response: {json.dumps(result, indent=2)}')
                    
                    # Check if the response is valid
                    if 'result' in result and 'prompts' in result['result']:
                        prompts = result['result']['prompts']
                        print(f'\n✅ Success! Found {len(prompts)} prompts')
                        print(f'First prompt: {prompts[0]["name"]} - {prompts[0]["description"]}')
                    elif 'error' in result:
                        print(f'\n❌ Error: {result["error"]["message"]}')
                    else:
                        print('\n❓ Unknown response format')
                else:
                    print(f'Error response: {await response.text()}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_service_endpoint())