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
    const response = await fetch('/services');
    const data = await response.json();
    
    if (data && data.services) {
      renderServices(data.services);
    } else {
      showError('Failed to load services data');
    }
  } catch (error) {
    console.error('Error fetching services:', error);
    showError('Failed to connect to the API');
  }
}

// Render services in the service list
function renderServices(services) {
  const serviceList = document.getElementById('service-list');
  serviceList.innerHTML = '';
  
  if (services.length === 0) {
    serviceList.innerHTML = '<p>No services available at the moment.</p>';
    return;
  }
  
  services.forEach(service => {
    const serviceCard = document.createElement('div');
    serviceCard.className = 'service-card';
    
    const toolsList = service.tools.map(tool => 
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
}

// Fetch detailed information about a specific service
async function fetchServiceDetails(serviceName) {
  try {
    const response = await fetch(`/services/${serviceName}`);
    const data = await response.json();
    
    // Show service details in a modal or expandable section
    showServiceDetails(data);
  } catch (error) {
    console.error(`Error fetching details for ${serviceName}:`, error);
    showError(`Failed to load details for ${serviceName}`);
  }
}

// Show service details in a modal
function showServiceDetails(service) {
  // Create modal content
  const modalContent = `
    <h3>${service.name} Service (${service.version})</h3>
    <p>${service.description}</p>
    <h4>Status: <span class="status-${service.status}">${service.status}</span></h4>
    
    <h4>Available Tools:</h4>
    <ul>
      ${service.tools.map(tool => `
        <li>
          <strong>${tool.name}</strong>: ${tool.description}
        </li>
      `).join('')}
    </ul>
    
    <h4>Available Versions:</h4>
    <ul>
      ${service.available_versions.map(v => `<li>${v}</li>`).join('')}
    </ul>
  `;
  
  // Show modal with the content
  const modal = document.getElementById('service-modal');
  const modalBody = document.getElementById('service-modal-content');
  
  modalBody.innerHTML = modalContent;
  modal.style.display = 'block';
  
  // Close modal when clicking the close button
  const closeBtn = document.getElementsByClassName('close-modal')[0];
  closeBtn.onclick = function() {
    modal.style.display = 'none';
  };
  
  // Close modal when clicking outside of it
  window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = 'none';
    }
  };
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