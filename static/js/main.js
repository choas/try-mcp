// Main JavaScript for the multi-service MCP platform landing page

document.addEventListener('DOMContentLoaded', function() {
  // Fetch services from the API
  fetchServices();
  
  // Set up code tabs
  setupCodeTabs();
});

// Fetch services from the API
async function fetchServices() {
  try {
    console.log('Fetching services from /services endpoint...');
    
    // Use XMLHttpRequest for better compatibility
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/services', true);
    
    xhr.onload = function() {
      if (xhr.status >= 200 && xhr.status < 300) {
        console.log('Response received:', xhr.responseText);
        
        try {
          const data = JSON.parse(xhr.responseText);
          console.log('Parsed data:', data);
          
          if (data && data.services) {
            console.log(`Found ${data.services.length} services`);
            renderServices(data.services);
            
            // Generate Claude Desktop configuration
            generateClaudeDesktopConfig(data.services);
          } else {
            console.error('No services found in the response:', data);
            showError('Failed to load services data. Check the console for details.');
          }
        } catch (parseError) {
          console.error('Error parsing JSON:', parseError);
          showError('Failed to parse service data');
        }
      } else {
        console.error('Request failed with status:', xhr.status);
        showError(`Failed to load services: HTTP ${xhr.status}`);
      }
    };
    
    xhr.onerror = function() {
      console.error('Network error occurred');
      showError('Network error while fetching services');
    };
    
    xhr.send();
  } catch (error) {
    console.error('Error fetching services:', error);
    showError(`Failed to connect to the API: ${error.message}`);
  }
}

// Render services in the service list
function renderServices(services) {
  console.log('Rendering services:', services);
  const serviceList = document.getElementById('service-list');
  
  if (!serviceList) {
    console.error('Service list element not found!');
    return;
  }
  
  serviceList.innerHTML = '';
  
  if (services.length === 0) {
    serviceList.innerHTML = '<p>No services available at the moment.</p>';
    return;
  }
  
  services.forEach(service => {
    console.log('Rendering service:', service.name);
    const serviceCard = document.createElement('div');
    serviceCard.className = 'service-card';
    
    // Check if tools array exists
    const tools = service.tools || [];
    console.log(`Service ${service.name} has ${tools.length} tools`);
    
    const toolsList = tools.map(tool => 
      `<li class="tool-item">${tool.name}</li>`
    ).join('');
    
    serviceCard.innerHTML = `
      <div class="service-header">
        <div class="service-name">${service.name}</div>
        <div class="service-version">${service.version}</div>
      </div>
      <div class="service-body">
        <div class="service-description">${service.description}</div>
        <div class="service-tools">
          <h4>Available Tools:</h4>
          <ul class="tool-list">
            ${toolsList}
          </ul>
        </div>
        <button class="details-btn" onclick="fetchServiceDetails('${service.name}')">View Details</button>
      </div>
    `;
    
    serviceList.appendChild(serviceCard);
  });
  
  console.log('Services rendering complete');
}

// Fetch detailed information about a specific service
async function fetchServiceDetails(serviceName) {
  try {
    console.log(`Fetching details for service: ${serviceName}`);
    const xhr = new XMLHttpRequest();
    xhr.open('GET', `/services/${serviceName}`, true);
    
    xhr.onload = function() {
      if (xhr.status >= 200 && xhr.status < 300) {
        console.log(`Service details received for ${serviceName}:`, xhr.responseText);
        
        try {
          const data = JSON.parse(xhr.responseText);
          showServiceDetails(data);
        } catch (parseError) {
          console.error('Error parsing service details JSON:', parseError);
          showError(`Failed to parse details for ${serviceName}`);
        }
      } else {
        console.error(`Request failed for ${serviceName} with status:`, xhr.status);
        showError(`Failed to load details for ${serviceName}: HTTP ${xhr.status}`);
      }
    };
    
    xhr.onerror = function() {
      console.error(`Network error occurred while fetching details for ${serviceName}`);
      showError(`Network error while fetching details for ${serviceName}`);
    };
    
    xhr.send();
  } catch (error) {
    console.error(`Error fetching details for ${serviceName}:`, error);
    showError(`Failed to load details for ${serviceName}: ${error.message}`);
  }
}

// Show service details at the bottom of the page
function showServiceDetails(service) {
  console.log('Showing service details:', service);
  
  // Create details content
  const detailsContent = `
    <div class="service-details-card">
      <h3>${service.name} Service (${service.version})</h3>
      <p>${service.description}</p>
      <div class="service-status">
        <h4>Status: <span class="status-${service.status}">${service.status}</span></h4>
      </div>
      
      <div class="service-tools-detail">
        <h4>Available Tools:</h4>
        <ul class="tools-detail-list">
          ${service.tools.map(tool => `
            <li class="tool-detail-item">
              <div class="tool-name">${tool.name}</div>
              <div class="tool-description">${tool.description || 'No description available'}</div>
            </li>
          `).join('')}
        </ul>
      </div>
      
      <div class="service-versions">
        <h4>Available Versions:</h4>
        <ul class="versions-list">
          ${service.available_versions.map(v => `<li class="version-item">${v}</li>`).join('')}
        </ul>
      </div>
      
      <button class="close-details-btn" onclick="hideServiceDetails()">Close Details</button>
    </div>
  `;
  
  // Show details at the bottom of the page
  const detailsSection = document.getElementById('service-details');
  detailsSection.innerHTML = detailsContent;
  detailsSection.style.display = 'block';
  
  // Scroll to the details section
  detailsSection.scrollIntoView({ behavior: 'smooth' });
}

// Hide service details
function hideServiceDetails() {
  const detailsSection = document.getElementById('service-details');
  detailsSection.style.display = 'none';
}

// Set up code tabs
function setupCodeTabs() {
  const tabs = document.querySelectorAll('.code-tab');
  const examples = document.querySelectorAll('.code-example');
  
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Remove active class from all tabs and examples
      tabs.forEach(t => t.classList.remove('active'));
      examples.forEach(e => e.classList.remove('active'));
      
      // Add active class to clicked tab and corresponding example
      tab.classList.add('active');
      const target = tab.getAttribute('data-target');
      document.getElementById(target).classList.add('active');
    });
  });
}

// Show error message
function showError(message) {
  const serviceList = document.getElementById('service-list');
  serviceList.innerHTML = `<div class="error-message">${message}</div>`;
}

// Generate Claude Desktop configuration based on available services
function generateClaudeDesktopConfig(services) {
  console.log('Generating Claude Desktop configuration for', services.length, 'services');
  
  // Get the Claude example element
  const claudeExample = document.getElementById('claude-example');
  if (!claudeExample) {
    console.error('Claude example element not found');
    return;
  }
  
  // Create the configuration object
  const mcpServers = {};
  
  // Add each service to the configuration
  services.forEach(service => {
    // Create a server name based on the service name
    const serverName = `try-mcp-${service.name}`;
    
    // Get the first tool from each service for autoApprove
    const autoApproveTools = service.tools.map(tool => tool.name);
    
    // Add the service to the configuration
    mcpServers[serverName] = {
      "command": "npx",
      "args": [`mcp-remote`, `https://try-mcp.dev/services/${service.name}/${service.version}`],
      "disabled": false,
      "autoApprove": autoApproveTools
    };
  });
  
  // Create the configuration JSON
  const config = {
    mcpServers: mcpServers
  };
  
  // Format the configuration as a string with proper indentation
  const configStr = JSON.stringify(config, null, 2);
  
  // Create the complete example content
  const exampleContent = `
{
${configStr.substring(1, configStr.length - 1)}
}

// To use in Claude Desktop:
// 1. Open Claude Desktop settings
// 2. Navigate to the MCP section
// 3. Add the above configuration
// 4. Save and restart Claude Desktop
// 5. Now you can use the services directly in your conversations

// Example usage in Claude:
// "What's the weather forecast for Berlin tomorrow?"
// Claude will use the get_weather_forecast tool automatically

// For more information about MCP configuration, visit:
// https://docs.anthropic.com/claude/docs/mcp-configuration
`;

  // Update the Claude example content
  const codeElement = claudeExample.querySelector('code');
  if (codeElement) {
    codeElement.textContent = exampleContent;
    console.log('Claude Desktop configuration updated');
  } else {
    console.error('Code element not found in Claude example');
  }
}