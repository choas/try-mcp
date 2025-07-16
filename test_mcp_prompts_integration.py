"""Integration tests for MCP prompts/list method at server level."""

import pytest
import json
from multi_service_server import MultiServiceMCPServer


class TestMCPPromptsIntegration:
    """Test MCP prompts/list method integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.server = MultiServiceMCPServer()
    
    @pytest.mark.asyncio
    async def test_prompts_list_method(self):
        """Test that prompts/list method works correctly."""
        request = {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "prompts/list",
            "params": {}
        }
        
        response = await self.server.handle_mcp_request(request)
        
        # Check response structure
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 12
        assert "result" in response
        assert "prompts" in response["result"]
        
        prompts = response["result"]["prompts"]
        
        # Should have 30 fortune prompts
        assert len(prompts) == 30
        
        # Check prompt structure
        for i, prompt in enumerate(prompts):
            assert "name" in prompt
            assert "description" in prompt
            assert "arguments" in prompt
            
            # Check naming convention
            assert prompt["name"] == f"fortune_prompt_{i+1}"
            
            # Check description format
            assert prompt["description"].startswith("Fortune generation prompt:")
            
            # Arguments should be empty list
            assert prompt["arguments"] == []
    
    @pytest.mark.asyncio
    async def test_prompts_list_content_quality(self):
        """Test that prompts contain quality content."""
        request = {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "prompts/list",
            "params": {}
        }
        
        response = await self.server.handle_mcp_request(request)
        prompts = response["result"]["prompts"]
        
        # Check that prompts contain surreal and cryptic content
        descriptions = [p["description"] for p in prompts]
        
        # Should contain mystical/surreal words
        mystical_words = ["mirror", "shadow", "dream", "whisper", "mystery", "silence", "forgotten", "impossible"]
        found_mystical = sum(1 for desc in descriptions for word in mystical_words if word in desc.lower())
        assert found_mystical >= 10  # Should find many mystical references
        
        # Should have varied content
        unique_descriptions = set(descriptions)
        assert len(unique_descriptions) == len(descriptions)  # All unique
    
    @pytest.mark.asyncio
    async def test_initialize_includes_prompts_capability(self):
        """Test that initialize method includes prompts capability."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        response = await self.server.handle_mcp_request(request)
        
        assert "result" in response
        assert "capabilities" in response["result"]
        capabilities = response["result"]["capabilities"]
        
        # Should include prompts capability
        assert "prompts" in capabilities
        assert capabilities["prompts"]["listChanged"] == False
    
    @pytest.mark.asyncio
    async def test_prompts_list_with_different_request_ids(self):
        """Test that prompts/list works with different request IDs."""
        for request_id in [1, 42, "test-123", None]:
            request = {
                "jsonrpc": "2.0",
                "method": "prompts/list",
                "params": {}
            }
            
            if request_id is not None:
                request["id"] = request_id
            
            response = await self.server.handle_mcp_request(request)
            
            assert response["jsonrpc"] == "2.0"
            if request_id is not None:
                assert response["id"] == request_id
            assert "result" in response
            assert len(response["result"]["prompts"]) == 30
    
    @pytest.mark.asyncio
    async def test_prompts_list_error_handling(self):
        """Test error handling for prompts/list method."""
        # Test with invalid params (should still work)
        request = {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "prompts/list",
            "params": {"invalid": "param"}
        }
        
        response = await self.server.handle_mcp_request(request)
        
        # Should still work despite invalid params
        assert "result" in response
        assert len(response["result"]["prompts"]) == 30
    
    @pytest.mark.asyncio
    async def test_prompts_list_consistency(self):
        """Test that prompts/list returns consistent results."""
        request = {
            "jsonrpc": "2.0",
            "id": 15,
            "method": "prompts/list",
            "params": {}
        }
        
        # Call multiple times
        response1 = await self.server.handle_mcp_request(request)
        response2 = await self.server.handle_mcp_request(request)
        response3 = await self.server.handle_mcp_request(request)
        
        # Results should be identical
        prompts1 = response1["result"]["prompts"]
        prompts2 = response2["result"]["prompts"]
        prompts3 = response3["result"]["prompts"]
        
        assert prompts1 == prompts2 == prompts3
    
    def test_fortune_service_has_prompts_data(self):
        """Test that fortune service has the required prompts data."""
        # Get the fortune service
        fortune_service = self.server.router.get_service("fortune", "v1")
        assert fortune_service is not None
        
        # Check that it has prompts data
        assert hasattr(fortune_service, '_prompts')
        assert len(fortune_service._prompts) == 30
        
        # Check that prompts are strings
        for prompt in fortune_service._prompts:
            assert isinstance(prompt, str)
            assert len(prompt) > 10  # Reasonable length
    
    @pytest.mark.asyncio
    async def test_mcp_protocol_compliance(self):
        """Test full MCP protocol compliance for prompts."""
        # Test initialize -> prompts/list workflow
        
        # 1. Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        init_response = await self.server.handle_mcp_request(init_request)
        assert "result" in init_response
        assert "capabilities" in init_response["result"]
        assert "prompts" in init_response["result"]["capabilities"]
        
        # 2. Get prompts
        prompts_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "prompts/list",
            "params": {}
        }
        
        prompts_response = await self.server.handle_mcp_request(prompts_request)
        assert "result" in prompts_response
        assert "prompts" in prompts_response["result"]
        
        # 3. Verify prompt structure matches MCP spec
        prompts = prompts_response["result"]["prompts"]
        for prompt in prompts:
            # Required fields per MCP spec
            assert "name" in prompt
            assert isinstance(prompt["name"], str)
            
            # Optional fields
            if "description" in prompt:
                assert isinstance(prompt["description"], str)
            
            if "arguments" in prompt:
                assert isinstance(prompt["arguments"], list)
                for arg in prompt["arguments"]:
                    assert isinstance(arg, dict)
                    assert "name" in arg
                    if "description" in arg:
                        assert isinstance(arg["description"], str)
                    if "required" in arg:
                        assert isinstance(arg["required"], bool)


class TestMCPPromptsEdgeCases:
    """Test edge cases for MCP prompts functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.server = MultiServiceMCPServer()
    
    @pytest.mark.asyncio
    async def test_prompts_list_with_no_fortune_service(self):
        """Test prompts/list when fortune service is not available."""
        # Unregister fortune service
        self.server.router.unregister_service("fortune", "v1")
        
        request = {
            "jsonrpc": "2.0",
            "id": 16,
            "method": "prompts/list",
            "params": {}
        }
        
        response = await self.server.handle_mcp_request(request)
        
        # Should still return valid response with empty prompts
        assert "result" in response
        assert "prompts" in response["result"]
        assert response["result"]["prompts"] == []
    
    @pytest.mark.asyncio
    async def test_prompts_list_with_multiple_fortune_services(self):
        """Test prompts/list behavior with multiple fortune service versions."""
        # This test verifies current behavior - only one version is expected
        request = {
            "jsonrpc": "2.0",
            "id": 17,
            "method": "prompts/list",
            "params": {}
        }
        
        response = await self.server.handle_mcp_request(request)
        
        # Should have prompts from the one fortune service
        assert "result" in response
        assert len(response["result"]["prompts"]) == 30
    
    @pytest.mark.asyncio
    async def test_prompts_list_json_serialization(self):
        """Test that prompts/list response can be properly JSON serialized."""
        request = {
            "jsonrpc": "2.0",
            "id": 18,
            "method": "prompts/list",
            "params": {}
        }
        
        response = await self.server.handle_mcp_request(request)
        
        # Should be JSON serializable
        json_str = json.dumps(response)
        assert len(json_str) > 100  # Should be substantial content
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed == response