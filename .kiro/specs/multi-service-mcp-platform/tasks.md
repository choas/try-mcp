# Implementation Plan

- [x] 1. Create core infrastructure and base service interface
  - Implement base service abstract class with common interface methods
  - Create service request/response data models using dataclasses
  - Set up project structure with services, utils, and data directories
  - _Requirements: 1.1, 1.3, 7.1_

- [ ] 2. Implement service router and request handling
  - Create service router class to parse URLs and route requests to appropriate services
  - Implement URL pattern matching for `/<service>/<version>` structure
  - Add service registration and discovery mechanism
  - Write unit tests for routing logic and URL parsing
  - _Requirements: 1.1, 1.4, 7.3_

- [ ] 3. Refactor existing MVG service to new architecture
  - Extract MVG functionality from existing mcp_server.py into new MVG service class
  - Implement MVG service using base service interface
  - Maintain backward compatibility with existing tool definitions
  - Write unit tests for MVG service integration
  - _Requirements: 1.2, 7.1_

- [ ] 4. Implement mindful sentences service
  - Create mindful sentences data pool with 50+ inspirational sentences
  - Implement daily sentence rotation logic to ensure 4 different sentences per day
  - Create mindful service class with get_mindful_sentence tool
  - Write unit tests for sentence selection and daily rotation logic
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 5. Implement optimistic weather forecast service
  - Create weather service class that always returns pleasant weather predictions
  - Implement temperature range logic (18-24°C) and sunny/partly cloudy conditions
  - Create get_weather_forecast tool with consistent optimistic responses
  - Write unit tests to verify weather predictions are always positive
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 6. Implement emoji oracle service
  - Create emoji symbol pool with diverse meaningful symbols organized by categories
  - Implement random 3-emoji combination generator with cryptic message logic
  - Create emoji oracle service class with get_emoji_oracle tool
  - Write unit tests for emoji selection and combination uniqueness
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 7. Implement random timestamp service
  - Create timestamp service class with range validation logic
  - Implement random timestamp generation within specified start/end ranges
  - Add default range handling (current year) and ISO 8601 formatting
  - Write unit tests for timestamp generation, range validation, and error handling
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 8. Implement digital fortune cookie service
  - Create fortune phrase generator with surreal and cryptic content templates
  - Implement hourly caching mechanism to ensure same phrase per hour
  - Create fortune cookie service class with get_fortune_cookie tool
  - Write unit tests for phrase generation, caching, and hourly rotation
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 9. Implement error handling and response formatting
  - Create standardized error response formatter with structured error codes
  - Implement error handling middleware for service router
  - Add comprehensive logging for requests, responses, and errors
  - Write unit tests for error scenarios and response formatting
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 10. Create unified MCP server with multi-service support
  - Integrate service router into main MCP server class
  - Update server initialization to register all available services
  - Maintain MCP protocol compliance for tools/list and tools/call methods
  - Write integration tests for complete request/response flow
  - _Requirements: 1.1, 1.3, 7.4_

- [ ] 11. Add configuration management and service enablement
  - Create configuration system for enabling/disabling individual services
  - Implement service status reporting and health checks
  - Add environment variable support for configuration options
  - Write unit tests for configuration loading and service management
  - _Requirements: 7.4, 1.4_

- [ ] 12. Create comprehensive test suite and documentation
  - Write integration tests for all service endpoints and MCP protocol compliance
  - Create test fixtures for sample requests and expected responses
  - Add performance tests for concurrent request handling
  - Update project documentation with new service descriptions and usage examples
  - _Requirements: 1.3, 7.1, 7.2_