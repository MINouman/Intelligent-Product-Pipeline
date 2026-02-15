// Dashboard JavaScript

// Load data from JSON files
async function loadData() {
    try {
        const [normalized, enriched, duplicates, validated] = await Promise.all([
            fetch('../data/output/normalized_products.json').then(r => r.json()),
            fetch('../data/output/enriched_products.json').then(r => r.json()),
            fetch('../data/output/duplicates.json').then(r => r.json()),
            fetch('../data/output/validated_products.json').then(r => r.json())
        ]);

        updateMetrics(normalized, enriched, duplicates, validated);
        createQualityChart(validated);
        createMethodsChart(duplicates);
        updateVendorStats(normalized);
    } catch (error) {
        console.error('Error loading data:', error);
        showError();
    }
}

function updateMetrics(normalized, enriched, duplicates, validated) {
    document.getElementById('normalized-count').textContent = normalized.length;
    document.getElementById('enriched-count').textContent = enriched.length;
    document.getElementById('duplicate-count').textContent = duplicates.length;
    document.getElementById('validated-count').textContent = validated.length;
    
    const successRate = (normalized.length / 1000 * 100).toFixed(1);
    document.getElementById('norm-rate').textContent = successRate;
}

function createQualityChart(validated) {
    const qualityLevels = validated.reduce((acc, product) => {
        const level = product.quality_level;
        acc[level] = (acc[level] || 0) + 1;
        return acc;
    }, {});

    const ctx = document.getElementById('qualityChart');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Excellent', 'Good', 'Fair', 'Poor'],
            datasets: [{
                label: 'Products',
                data: [
                    qualityLevels['Excellent'] || 0,
                    qualityLevels['Good'] || 0,
                    qualityLevels['Fair'] || 0,
                    qualityLevels['Poor'] || 0
                ],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(23, 162, 184, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(220, 53, 69, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function createMethodsChart(duplicates) {
    const methods = duplicates.reduce((acc, group) => {
        const method = group.method || 'none';
        acc[method] = (acc[method] || 0) + 1;
        return acc;
    }, {});

    const ctx = document.getElementById('methodsChart');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(methods),
            datasets: [{
                data: Object.values(methods),
                backgroundColor: [
                    'rgba(13, 110, 253, 0.8)',
                    'rgba(25, 135, 84, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(220, 53, 69, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function updateVendorStats(normalized) {
    const vendors = normalized.reduce((acc, product) => {
        const vendor = product.vendor_id;
        acc[vendor] = (acc[vendor] || 0) + 1;
        return acc;
    }, {});

    const container = document.getElementById('vendor-stats');
    container.innerHTML = Object.entries(vendors)
        .map(([vendor, count]) => `
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <h6 class="text-muted">Vendor ${vendor}</h6>
                        <h3 class="mb-0">${count}</h3>
                        <small class="text-success">
                            <i class="bi bi-check-circle-fill"></i> Active
                        </small>
                    </div>
                </div>
            </div>
        `).join('');
}

function showError() {
    document.querySelector('.container').innerHTML = `
        <div class="alert alert-warning" role="alert">
            <h4 class="alert-heading">Data Not Found</h4>
            <p>Please run the pipeline first:</p>
            <code>python -m src.cli.commands pipeline</code>
        </div>
    `;
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadData);