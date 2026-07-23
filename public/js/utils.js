// Get JWT token from localStorage
function getToken() {
  return localStorage.getItem('token');
}

// Get current user info
function getUser() {
  return JSON.parse(localStorage.getItem('user'));
}

// API call helper
async function apiCall(endpoint, method = 'GET', data = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    }
  };
  
  if (data) {
    options.body = JSON.stringify(data);
  }
  
  try {
    const response = await fetch(endpoint, options);
    
    // If unauthorized, clear storage and redirect to login
    if (response.status === 401) {
      localStorage.clear();
      window.location.href = '/login.html';
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return null;
  }
}

// Show success/error message
function showMsg(elementId, message, isError = true) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  element.textContent = message;
  element.style.display = 'block';
  element.className = isError ? 'error-msg' : 'success-msg';
  
  setTimeout(() => {
    element.style.display = 'none';
  }, 5000);
}

// Build query string from parameters
function buildQuery(params) {
  const q = new URLSearchParams();
  Object.keys(params).forEach(key => {
    if (params[key]) {
      q.append(key, params[key]);
    }
  });
  return q.toString();
}

// Export data to Excel/PDF/Word
async function exportData(format) {
  const filters = {
    fuel_type: document.getElementById('filterFuelType')?.value,
    transaction_type: document.getElementById('filterTransactionType')?.value,
    date_from: document.getElementById('filterDateFrom')?.value,
    date_to: document.getElementById('filterDateTo')?.value,
    search: document.getElementById('searchBox')?.value
  };
  
  const queryString = buildQuery(filters);
  const url = `/api/export/${format}?${queryString}`;
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    
    if (!response.ok) {
      throw new Error('Export failed');
    }
    
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    
    const ext = format === 'excel' ? 'xlsx' : format === 'word' ? 'docx' : 'pdf';
    link.download = `Fuel_Report.${ext}`;
    link.click();
    
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    alert('Export failed: ' + error.message);
  }
}

// Logout user
function logout() {
  if (confirm('Are you sure you want to logout?')) {
    localStorage.clear();
    window.location.href = '/login.html';
  }
}

// Check if user is authenticated
function checkAuth() {
  if (!getToken()) {
    window.location.href = '/login.html';
  }
}
