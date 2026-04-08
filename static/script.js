// main script for smartdata app

// form submission
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registrationForm');
    const datasetFile = document.getElementById('datasetFile');
    const fileStatus = document.getElementById('fileStatus');
    const selectedFileName = document.getElementById('selectedFileName');
    
    // file selection feedback
    if (datasetFile) {
        datasetFile.addEventListener('change', () => {
            if (datasetFile.files && datasetFile.files[0]) {
                selectedFileName.textContent = datasetFile.files[0].name;
                fileStatus.classList.remove('hidden');
            } else {
                fileStatus.classList.add('hidden');
            }
        });
    }
    
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
});

// handle form submission
function handleFormSubmit(e) {
    e.preventDefault();
    
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const password = document.getElementById('password').value.trim();
    const datasetFile = document.getElementById('datasetFile');
    
    // clear previous errors and results
    clearErrors();
    document.getElementById('resultBox').classList.add('hidden');
    document.getElementById('processResult').classList.add('hidden');
    
    // basic validation
    if (!name || !email || !phone || !password) {
        showError('name', 'All fields required');
        return;
    }
    
    // show loading
    showLoading();
    
    // send to backend
    const data = {
        name: name,
        email: email,
        phone: phone,
        password: password
    };
    
    fetch('/api/validate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        showResults(result);
        
        // if file selected, process it automatically with user_id
        if (datasetFile.files && datasetFile.files[0]) {
            processDatasetFile(datasetFile.files[0], result.user_id);
        } else {
            hideLoading();
        }
    })
    .catch(error => {
        hideLoading();
        showError('name', 'Server error: ' + error.message);
    });
}

// process dataset file automatically after registration
function processDatasetFile(file, userId) {
    const formData = new FormData();
    formData.append('file', file);
    if (userId) {
        formData.append('user_id', userId);
    }

    console.log('Uploading file:', file.name, 'for user:', userId);

    fetch('/api/process', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Response status:', response.status, response.statusText);
        if (!response.ok) {
            // try to get error message from response
            return response.json().then(data => {
                throw new Error(data.error || `Upload failed: ${response.statusText}`);
            }).catch(e => {
                throw new Error(`Upload failed: ${response.statusText}`);
            });
        }
        return response.json();
    })
    .then(result => {
        console.log('Process result:', result);
        hideLoading();
        if (result.error) {
            throw new Error(result.error);
        }
        displayProcessResults(result);
    })
    .catch(error => {
        console.error('Upload error:', error);
        hideLoading();
        const processResult = document.getElementById('processResult');
        processResult.classList.remove('hidden');
        processResult.innerHTML = `<div style="color: #e74c3c; padding: 15px; background: #ffe6e6; border: 1px solid #ff9999; border-radius: 4px;"><strong>Error:</strong> ${error.message}</div>`;
    });
}

// show validation results
function showResults(result) {
    const resultBox = document.getElementById('resultBox');
    const resultContent = document.getElementById('resultContent');
    
    let html = '';
    
    // Use 'fields' from backend response (not 'results')
    const validationResults = result.fields || result.results || {};
    
    for (let field in validationResults) {
        const validation = validationResults[field];
        const isValid = validation.valid ? 'valid' : 'invalid';
        const icon = validation.valid ? '✓' : '✗';
        
        html += `
            <div class="result-item">
                <span class="result-label">${field}</span>
                <span class="result-value ${isValid}">${icon} ${validation.message || (validation.valid ? 'Valid' : 'Invalid')}</span>
            </div>
        `;
    }
    
    if (html === '') {
        html = '<div class="result-item"><span>All fields are valid!</span></div>';
    }
    
    resultContent.innerHTML = html;
    resultBox.classList.remove('hidden');
}

// show error message
function showError(fieldId, message) {
    const errorSpan = document.getElementById(fieldId + '-error');
    if (errorSpan) {
        errorSpan.textContent = message;
    }
}

// clear all errors
function clearErrors() {
    const errorSpans = document.querySelectorAll('.error-msg');
    errorSpans.forEach(span => {
        span.textContent = '';
    });
}

// show loading state
function showLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.classList.remove('hidden');
    }
}

// hide loading state
function hideLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.classList.add('hidden');
    }
}

// display process results
function displayProcessResults(result) {
    const processResult = document.getElementById('processResult');
    processResult.classList.remove('hidden');

    let html = `<h4>✓ Dataset Processed Successfully</h4>`;

    // stats
    if (result.stats) {
        html += `
            <div class="result-stat"><strong>Rows:</strong> ${result.stats.row_count || 0}</div>
            <div class="result-stat"><strong>Columns:</strong> ${result.stats.column_count || 0}</div>
            <div class="result-stat"><strong>Missing Values:</strong> ${result.stats.missing_values || 0}</div>
        `;
    }

    // threading
    if (result.threading_info) {
        html += `<div class="result-stat"><strong>Threading:</strong> ${result.threading_info.num_threads || 0} threads completed</div>`;
    }

    // column stats preview
    if (result.stats && result.stats.column_stats) {
        const colStats = result.stats.column_stats;
        const cols = Object.keys(colStats).slice(0, 3);
        if (cols.length > 0) {
            html += `<div style="margin-top: 10px;"><strong>Column Statistics (Preview):</strong></div>`;
            cols.forEach(col => {
                const stats = colStats[col];
                html += `
                    <div class="result-stat">
                        <strong>${col}:</strong> 
                        Mean=${(stats.mean || 0).toFixed(2)}, 
                        Median=${(stats.median || 0).toFixed(2)}, 
                        Std=${(stats.std || 0).toFixed(2)}
                    </div>
                `;
            });
        }
    }

    // charts - with better debugging
    if (result.charts && result.charts.length > 0) {
        console.log('Displaying', result.charts.length, 'charts:', result.charts);
        html += `<div class="chart-display"><strong>Generated Charts:</strong><br/>`;
        result.charts.forEach((chartPath, idx) => {
            // fix: ensure path includes /static prefix
            let fullPath = chartPath;
            if (!fullPath.startsWith('/static/')) {
                fullPath = '/static/' + chartPath;
            }
            console.log(`Chart ${idx}:`, fullPath);
            html += `
            <div style="margin-top: 20px; padding: 10px; background: #fafafa; border: 1px solid #ddd; border-radius: 4px; min-height: 300px;">
                <img src="${fullPath}" 
                     alt="Chart ${idx}" 
                     style="width: 100%; max-width: 100%; height: auto; display: block; border: 1px solid #ddd; border-radius: 4px;" 
                     data-chart-idx="${idx}">
                <p style="font-size: 12px; color: #999; margin-top: 10px;">Path: ${fullPath}</p>
            </div>`;
        });
        html += `</div>`;
    } else {
        console.log('No charts in response');
        html += `<div class="result-stat">No charts generated</div>`;
    }

    processResult.innerHTML = html;
    
    // Attach event listeners to images
    const images = processResult.querySelectorAll('img');
    images.forEach((img, idx) => {
        img.onload = function() {
            console.log('Chart loaded successfully:', img.src);
            img.parentElement.style.borderColor = '#4caf50';
        };
        img.onerror = function() {
            console.error('Failed to load chart:', img.src);
            img.parentElement.style.borderColor = '#f44336';
            img.parentElement.innerHTML += '<p style="color: red; margin-top: 10px;">ERROR: Failed to load image</p>';
        };
    });
}

// load dashboard data
function loadDashboardData() {
    showLoading();
    
    fetch('/api/dashboard')
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to load dashboard data: ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        renderDashboard(data);
    })
    .catch(error => {
        hideLoading();
        console.error('Error loading dashboard:', error);
        alert('Error loading dashboard: ' + error.message);
    });
}

// render dashboard data
function renderDashboard(data) {
    // update stats
    if (data.stats) {
        document.getElementById('totalSubmissions').textContent = data.stats.total_users || 0;
        document.getElementById('validUsers').textContent = data.stats.valid_users || 0;
        document.getElementById('totalDatasets').textContent = data.stats.total_datasets || 0;
    }
    
    // render submissions table
    if (data.users && data.users.length > 0) {
        const tbody = document.getElementById('submissionsTable');
        tbody.innerHTML = '';
        
        data.users.forEach(user => {
            const date = new Date(user.submitted_at).toLocaleDateString();
            const status = user.status || 'submitted';
            
            tbody.innerHTML += `
                <tr>
                    <td><a href="#" class="user-link" onclick="viewUserCharts(${user.id}); return false;" style="color: #3498db; cursor: pointer; text-decoration: underline;">${user.name || '-'}</a></td>
                    <td>${user.email || '-'}</td>
                    <td>${user.phone || '-'}</td>
                    <td><span class="status">${status}</span></td>
                    <td>${date}</td>
                </tr>
            `;
        });
    }
    
    // render datasets
    if (data.datasets && data.datasets.length > 0) {
        const container = document.getElementById('datasetsContainer');
        container.innerHTML = '';
        
        data.datasets.forEach(dataset => {
            const card = `
                <div class="card">
                    <h5>${dataset.name || 'Dataset'}</h5>
                    <p>Processed: ${new Date(dataset.processed_at).toLocaleDateString()}</p>
                    ${dataset.charts && dataset.charts.length > 0 ? `<p>Charts: ${dataset.charts.length}</p>` : '<p>No charts</p>'}
                </div>
            `;
            container.innerHTML += card;
        });
    }
}

// view user charts in a modal
function viewUserCharts(userId) {
    showLoading();
    
    fetch(`/api/users/${userId}`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to load user data');
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        displayUserChartsModal(data);
    })
    .catch(error => {
        hideLoading();
        alert('Error loading user charts: ' + error.message);
    });
}

// display user charts in a modal
function displayUserChartsModal(data) {
    const user = data.user;
    const datasets = data.datasets || [];
    
    let html = `
        <div class="modal-overlay" onclick="closeModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2>${user.name}'s Datasets & Charts</h2>
                    <button class="modal-close" onclick="closeModal()">×</button>
                </div>
                <div class="modal-body">
    `;
    
    if (datasets.length === 0) {
        html += `<p style="text-align: center; color: #7f8c8d; padding: 20px;">No datasets uploaded by this user yet.</p>`;
    } else {
        datasets.forEach(dataset => {
            html += `
                <div class="dataset-section" style="margin-bottom: 30px;">
                    <h4 style="color: #2c3e50; margin-bottom: 15px;">Dataset: ${dataset.name}</h4>
                    <p style="font-size: 12px; color: #7f8c8d; margin-bottom: 10px;">Processed: ${new Date(dataset.processed_at).toLocaleDateString()}</p>
            `;
            
            if (dataset.charts && dataset.charts.length > 0) {
                dataset.charts.forEach(chartPath => {
                    let fullPath = chartPath;
                    if (!fullPath.startsWith('/static/')) {
                        fullPath = '/static/' + chartPath;
                    }
                    html += `<img src="${fullPath}" alt="Chart" style="width: 100%; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px;">`;
                });
            } else {
                html += `<p style="color: #7f8c8d;">No charts generated for this dataset.</p>`;
            }
            
            // show stats if available
            if (dataset.stats) {
                html += `
                    <div style="background: #f9f9f9; padding: 10px; border-radius: 4px; font-size: 12px; margin-top: 10px;">
                        <strong>Stats:</strong> ${dataset.stats.row_count || 0} rows, ${dataset.stats.column_count || 0} columns
                    </div>
                `;
            }
            
            html += `</div>`;
        });
    }
    
    html += `
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                </div>
            </div>
        </div>
    `;
    
    // create modal container
    let modal = document.getElementById('userChartsModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'userChartsModal';
        document.body.appendChild(modal);
    }
    
    modal.innerHTML = html;
    modal.style.display = 'block';
    
    // Attach event listeners to modal images
    const modalImages = modal.querySelectorAll('img');
    modalImages.forEach(img => {
        img.onload = function() {
            console.log('Modal chart loaded successfully:', img.src);
        };
        img.onerror = function() {
            console.error('Failed to load modal chart:', img.src);
            img.style.border = '2px solid #f44336';
        };
    });
}

// close modal
function closeModal() {
    const modal = document.getElementById('userChartsModal');
    if (modal) {
        modal.style.display = 'none';
    }
}
