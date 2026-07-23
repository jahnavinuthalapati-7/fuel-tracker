checkAuth();
document.addEventListener('DOMContentLoaded', init);

let allEntries = [];

function init() {
  const user = getUser();
  document.getElementById('username').textContent = user.username;
  document.getElementById('userRole').textContent = user.role;
  
  document.querySelector('.logout-btn').addEventListener('click', logout);
  
  document.getElementById('purchaseForm').addEventListener('submit', submitFuelEntry);
  document.getElementById('issueForm').addEventListener('submit', submitFuelEntry);
  
  document.getElementById('quantity').addEventListener('input', calcAmount);
  document.getElementById('rate').addEventListener('input', calcAmount);
  
  document.getElementById('opening_odometer').addEventListener('input', calcKMRun);
  document.getElementById('closing_odometer').addEventListener('input', calcKMRun);
  document.getElementById('km_run').addEventListener('change', calcMileage);
  document.getElementById('issue_quantity').addEventListener('change', calcMileage);
  
  document.getElementById('createUserForm').addEventListener('submit', createUser);
  document.getElementById('changePasswordForm').addEventListener('submit', changePassword);
  
  document.getElementById('dashboardSearch').addEventListener('input', searchDashboard);
  
  loadDashboard();
  loadReports();
  loadUsers();
}
function toggleStockInput() {
  const stockType = document.getElementById('stock_type').value;
  const stockInputGroup = document.getElementById('stockInputGroup');
  
  if (stockType === 'old' || stockType === 'new') {
    stockInputGroup.style.display = 'block';
  } else {
    stockInputGroup.style.display = 'none';
    document.getElementById('opening_stock').value = ''; 
  }
}
function switchPage(e, name) {
  e.preventDefault();
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
  document.getElementById(name).classList.add('active');
  e.target?.classList.add('active');
  
  if (name === 'dashboard') loadDashboard();
  else if (name === 'reports') loadReports();
  else if (name === 'manage-users') loadUsers();
}

function switchTab(e, tabId) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  e.target.classList.add('active');
}

async function loadDashboard() {
  const response = await apiCall('/api/dashboard');
  if (!response) return;
  
  const entries = await apiCall('/api/fuel-entries');
  allEntries = entries || [];
  
  const statsDiv = document.getElementById('statsDiv');
  statsDiv.innerHTML = response.stats.map(stat => {
    const fuelEntries = allEntries.filter(e => e.fuel_type === stat.fuel_type).sort((a, b) => new Date(a.date) - new Date(b.date));
    const oldStock = fuelEntries.length > 0 && fuelEntries[0].opening_stock ? fuelEntries[0].opening_stock : 0;
    const purchases = allEntries.filter(e => e.fuel_type === stat.fuel_type && e.transaction_type === 'Purchase').reduce((sum, e) => sum + (e.quantity || 0), 0);
    const allocated = allEntries.filter(e => e.fuel_type === stat.fuel_type && e.transaction_type === 'Issue').reduce((sum, e) => sum + (e.issue_quantity || 0), 0);
    const total = oldStock + purchases - allocated;
    
    return `
      <div class="stat-card">
        <div class="stat-label">${stat.fuel_type}</div>
        <div class="stat-value">${total.toFixed(2)}L</div>
        <div class="stat-breakdown">
          <div class="breakdown-box">
            <div class="box-label">Old Stock</div>
            <div class="box-value">${oldStock.toFixed(2)}L</div>
          </div>
          <div class="breakdown-box">
            <div class="box-label">Purchased</div>
            <div class="box-value">+${purchases.toFixed(2)}L</div>
          </div>
          <div class="breakdown-box">
            <div class="box-label">Allocated</div>
            <div class="box-value">-${allocated.toFixed(2)}L</div>
          </div>
          <div class="breakdown-box">
            <div class="box-label">TOTAL</div>
            <div class="box-value total">${total.toFixed(2)}L</div>
          </div>
        </div>
      </div>
    `;
  }).join('');
  
  loadRecent();
}

async function loadRecent() {
  const response = await apiCall('/api/fuel-entries');
  if (!response) return;
  
  const tbody = document.getElementById('recentTable');
  tbody.innerHTML = response.slice(0, 10).map(e => `
    <tr>
      <td>${e.date}</td>
      <td><span class="category-badge category-${e.transaction_type.toLowerCase()}">${e.transaction_type}</span></td>
      <td>${e.slip_no}</td>
      <td>${e.vehicle_no || '-'}</td>
      <td>${e.fuel_type}</td>
      <td>${(e.quantity || e.issue_quantity || 0).toFixed(2)}L</td>
      <td><button class="btn btn-danger btn-sm" onclick="deleteFuelEntry(${e.id})">Delete</button></td>
    </tr>
  `).join('');
}

async function searchDashboard() {
  const query = document.getElementById('dashboardSearch').value.toLowerCase();
  if (!query) {
    loadRecent();
    return;
  }
  
  const response = await apiCall('/api/fuel-entries');
  if (!response) return;
  
  const filtered = response.filter(e =>
    e.slip_no.toLowerCase().includes(query) ||
    (e.vehicle_no && e.vehicle_no.toLowerCase().includes(query)) ||
    (e.fuel_type && e.fuel_type.toLowerCase().includes(query)) ||
    (e.allocated_to && e.allocated_to.toLowerCase().includes(query)) ||
    (e.approved_by && e.approved_by.toLowerCase().includes(query))
  );
  
  const tbody = document.getElementById('recentTable');
  tbody.innerHTML = filtered.slice(0, 10).map(e => `
    <tr>
      <td>${e.date}</td>
      <td><span class="category-badge category-${e.transaction_type.toLowerCase()}">${e.transaction_type}</span></td>
      <td>${e.slip_no}</td>
      <td>${e.vehicle_no || '-'}</td>
      <td>${e.fuel_type}</td>
      <td>${(e.quantity || e.issue_quantity || 0).toFixed(2)}L</td>
      <td><button class="btn btn-danger btn-sm" onclick="deleteFuelEntry(${e.id})">Delete</button></td>
    </tr>
  `).join('');
}

function calcAmount() {
  const qty = parseFloat(document.getElementById('quantity').value) || 0;
  const rate = parseFloat(document.getElementById('rate').value) || 0;
  document.getElementById('amount').value = (qty * rate).toFixed(2);
}

function calcKMRun() {
  const opening = parseFloat(document.getElementById('opening_odometer').value) || 0;
  const closing = parseFloat(document.getElementById('closing_odometer').value) || 0;
  document.getElementById('km_run').value = (closing - opening).toFixed(2);
  calcMileage();
}

function calcMileage() {
  const km = parseFloat(document.getElementById('km_run').value) || 0;
  const issueQty = parseFloat(document.getElementById('issue_quantity').value) || 0;
  if (issueQty > 0) {
    document.getElementById('mileage').value = (km / issueQty).toFixed(2);
  }
}

async function submitFuelEntry(e) {
  e.preventDefault();
  const isPurchase = this.id === 'purchaseForm';
  
  const formData = {
    slip_no: isPurchase ? document.getElementById('slip_no_purchase').value : document.getElementById('slip_no_issue').value,
    transaction_type: isPurchase ? 'Purchase' : 'Issue',
    fuel_type: isPurchase ? document.getElementById('fuel_type_purchase').value : document.getElementById('fuel_type_issue').value,
    date: new Date().toISOString().split('T')[0],
    opening_stock: isPurchase ? parseFloat(document.getElementById('opening_stock').value) || null : null, 
    stock_type: isPurchase ? document.getElementById('stock_type').value : null,
    quantity: isPurchase ? parseFloat(document.getElementById('quantity').value) || null : null,  
    rate: isPurchase ? parseFloat(document.getElementById('rate').value) || null : null,
    amount: isPurchase ? parseFloat(document.getElementById('amount').value) || null : null,
    vendor_name: isPurchase ? document.getElementById('vendor_name').value : null,
    vendor_location: isPurchase ? document.getElementById('vendor_location').value : null,
    vehicle_no: !isPurchase ? document.getElementById('vehicle_no').value : null,
    vin_no: !isPurchase ? document.getElementById('vin_no').value : null,  
    registration_no: !isPurchase ? document.getElementById('registration_no').value : null,
    model_no: !isPurchase ? document.getElementById('model_no').value : null,
    allocated_to: !isPurchase ? document.getElementById('allocated_to').value : null,
    opening_odometer: !isPurchase ? parseFloat(document.getElementById('opening_odometer').value) || null : null,
    closing_odometer: !isPurchase ? parseFloat(document.getElementById('closing_odometer').value) || null : null,
    km_run: !isPurchase ? parseFloat(document.getElementById('km_run').value) || null : null,
    issue_quantity: !isPurchase ? parseFloat(document.getElementById('issue_quantity').value) || null : null,
    mileage: !isPurchase ? parseFloat(document.getElementById('mileage').value) || null : null,
    recipient_name: !isPurchase ? document.getElementById('recipient_name').value : null,
    receiver_name: !isPurchase ? document.getElementById('receiver_name').value : null,
    approved_by: isPurchase ? document.getElementById('approved_by_p').value : document.getElementById('approved_by_i').value,
    remarks: isPurchase ? document.getElementById('remarks_p').value : document.getElementById('remarks_i').value
  };
  
  const response = await apiCall('/api/fuel-entry', 'POST', formData);
  if (response && response.success) {
    showMsg(isPurchase ? 'purchaseMsg' : 'issueMsg', ' Entry saved!', false);
    this.reset();
    loadDashboard();
  } else {
    showMsg(isPurchase ? 'purchaseMsg' : 'issueMsg', ' Error saving entry');
  }
}

async function deleteFuelEntry(id) {
  if (!confirm('Delete this entry?')) return;
  const response = await apiCall(`/api/fuel-entry/${id}`, 'DELETE');
  if (response && response.success) {
    loadRecent();
    loadReports();
  }
}

async function loadReports() {
  const queryString = buildQuery({
    fuel_type: document.getElementById('filterFuelType')?.value,
    transaction_type: document.getElementById('filterTransactionType')?.value,
    date_from: document.getElementById('filterDateFrom')?.value,
    date_to: document.getElementById('filterDateTo')?.value,
    search: document.getElementById('searchBox')?.value
  });
  
  const response = await apiCall(`/api/fuel-entries?${queryString}`);
  if (!response) return;
  
  const tbody = document.getElementById('reportsTable');
  tbody.innerHTML = response.map(e => `
    <tr>
      <td>${e.date}</td>
      <td>${e.slip_no}</td>
      <td><span class="category-badge category-${e.transaction_type.toLowerCase()}">${e.transaction_type}</span></td>
      <td>${e.fuel_type}</td>
      <td>${e.vehicle_no || '-'}</td>
      <td>${e.vin_no || '-'}</td>
      <td>${e.registration_no || '-'}</td>
      <td>${e.model_no || '-'}</td>
      <td>${e.allocated_to || '-'}</td>
      <td>${e.opening_odometer || '-'}</td>
      <td>${e.closing_odometer || '-'}</td>
      <td>${e.km_run ? e.km_run.toFixed(2) : '-'}</td>
      <td>${(e.quantity || e.issue_quantity || 0).toFixed(2)}</td>
      <td>${e.mileage ? e.mileage.toFixed(2) : '-'}</td>
      <td>${e.approved_by || '-'}</td>
      <td>${e.receiver_name || '-'}</td>
      <td>${e.remarks || '-'}</td>
      <td><button class="btn btn-danger btn-sm" onclick="deleteFuelEntry(${e.id})">Delete</button></td>
    </tr>
  `).join('');
}

function clearFilters() {
  ['filterFuelType', 'filterTransactionType', 'filterDateFrom', 'filterDateTo', 'searchBox'].forEach(id => {
    const element = document.getElementById(id);
    if (element) element.value = '';
  });
  loadReports();
}

async function loadUsers() {
  const response = await apiCall('/api/users');
  if (!response) return;
  
  const tbody = document.getElementById('usersTable');
  tbody.innerHTML = response.map(user => `
    <tr>
      <td>${user.username}</td>
      <td>${user.role}</td>
      <td>${user.created_at}</td>
      <td><button class="btn btn-danger btn-sm" onclick="deleteUser(${user.id})">Delete</button></td>
    </tr>
  `).join('');
}

async function createUser(e) {
  e.preventDefault();
  const response = await apiCall('/api/users', 'POST', {
    username: document.getElementById('newUsername').value,
    password: document.getElementById('newPassword').value,
    role: document.getElementById('newRole').value
  });
  
  if (response && response.success) {
    showMsg('createUserMsg', ' User created!', false);
    document.getElementById('createUserForm').reset();
    loadUsers();
  } else {
    showMsg('createUserMsg', ' Error creating user');
  }
}

async function deleteUser(id) {
  if (!confirm('Delete this user?')) return;
  const response = await apiCall(`/api/users/${id}`, 'DELETE');
  if (response && response.success) loadUsers();
}

async function changePassword(e) {
  e.preventDefault();
  const oldPass = document.getElementById('oldPassword').value;
  const newPass = document.getElementById('newPasswordInput').value;
  const confirmPass = document.getElementById('confirmPassword').value;
  
  if (newPass !== confirmPass) {
    showMsg('changePasswordMsg', '❌ Passwords do not match');
    return;
  }
  
  const response = await apiCall('/api/change-password', 'POST', {
    oldPassword: oldPass,
    newPassword: newPass
  });
  
  if (response && response.success) {
    showMsg('changePasswordMsg', ' Password changed!', false);
    document.getElementById('changePasswordForm').reset();
  } else {
    showMsg('changePasswordMsg', ' Error changing password');
  }
}
