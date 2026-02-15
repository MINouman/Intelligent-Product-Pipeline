// Validation Report JavaScript - FIXED

let allProducts = [];

async function loadValidation() {
    try {
        const response = await fetch('/data/output/validated_products.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        allProducts = await response.json();
        
        updateSummary();
        displayProducts(allProducts);
    } catch (error) {
        console.error('Error loading validation:', error);
        document.getElementById('productsTable').innerHTML = `
            <tr><td colspan="4" class="text-center text-danger">
                Error loading validation data: ${error.message}<br>
                <small>Please ensure the pipeline has been run.</small>
            </td></tr>
        `;
    }
}

function updateSummary() {
    const counts = {
        'Excellent': 0,
        'Good': 0,
        'Fair': 0,
        'Poor': 0
    };
    
    allProducts.forEach(p => {
        const level = p.quality_level || 'Good';
        counts[level]++;
    });
    
    const total = allProducts.length || 1; // Prevent division by zero
    
    // Safely update DOM elements
    const excellentCount = document.getElementById('excellent-count');
    const excellentPct = document.getElementById('excellent-pct');
    const goodCount = document.getElementById('good-count');
    const goodPct = document.getElementById('good-pct');
    const fairCount = document.getElementById('fair-count');
    const fairPct = document.getElementById('fair-pct');
    const poorCount = document.getElementById('poor-count');
    const poorPct = document.getElementById('poor-pct');
    
    if (excellentCount) excellentCount.textContent = counts['Excellent'];
    if (excellentPct) excellentPct.textContent = `${(counts['Excellent']/total*100).toFixed(1)}%`;
    
    if (goodCount) goodCount.textContent = counts['Good'];
    if (goodPct) goodPct.textContent = `${(counts['Good']/total*100).toFixed(1)}%`;
    
    if (fairCount) fairCount.textContent = counts['Fair'];
    if (fairPct) fairPct.textContent = `${(counts['Fair']/total*100).toFixed(1)}%`;
    
    if (poorCount) poorCount.textContent = counts['Poor'];
    if (poorPct) poorPct.textContent = `${(counts['Poor']/total*100).toFixed(1)}%`;
}

function applyFilter() {
    const filter = document.getElementById('qualityFilter').value;
    
    const filtered = filter 
        ? allProducts.filter(p => p.quality_level === filter)
        : allProducts;
    
    displayProducts(filtered);
}

function displayProducts(products) {
    const tbody = document.getElementById('productsTable');
    
    if (!tbody) {
        console.error('Products table not found');
        return;
    }
    
    if (products.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted">
                    No products found.
                </td>
            </tr>
        `;
        return;
    }
    
    // Show first 50 products
    const display = products.slice(0, 50);
    
    tbody.innerHTML = display.map(product => {
        const issues = product.quality_issues || {};
        const issueList = Object.entries(issues)
            .filter(([_, v]) => v)
            .map(([k, _]) => k)
            .join(', ') || 'None';
        
        return `
            <tr>
                <td>
                    <strong>${product.name || 'Unknown Product'}</strong><br>
                    <small class="text-muted">Vendor: ${product.vendor_id || 'N/A'}</small>
                </td>
                <td>
                    <span class="badge ${getQualityBadge(product.quality_level)}">
                        ${product.quality_level || 'Good'}
                    </span>
                </td>
                <td>
                    <strong>${product.quality_score || 0}</strong>/100
                </td>
                <td>
                    <small>${issueList}</small>
                </td>
            </tr>
        `;
    }).join('');
    
    if (products.length > 50) {
        tbody.innerHTML += `
            <tr>
                <td colspan="4" class="text-center text-muted">
                    Showing first 50 of ${products.length} products
                </td>
            </tr>
        `;
    }
}

function getQualityBadge(level) {
    const badges = {
        'Excellent': 'bg-success',
        'Good': 'bg-info',
        'Fair': 'bg-warning',
        'Poor': 'bg-danger'
    };
    return badges[level] || 'bg-secondary';
}

document.addEventListener('DOMContentLoaded', loadValidation);