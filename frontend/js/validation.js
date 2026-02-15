// Validation Report JavaScript

let allProducts = [];

async function loadValidation() {
    try {
        const response = await fetch('../data/output/validated_products.json');
        allProducts = await response.json();
        
        updateSummary();
        displayProducts(allProducts);
    } catch (error) {
        document.getElementById('productsTable').innerHTML = `
            <tr><td colspan="4" class="text-center text-danger">
                Error loading validation data.
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
        counts[p.quality_level]++;
    });
    
    const total = allProducts.length;
    
    document.getElementById('excellent-count').textContent = counts['Excellent'];
    document.getElementById('excellent-pct').textContent = 
        `${(counts['Excellent']/total*100).toFixed(1)}%`;
    
    document.getElementById('good-count').textContent = counts['Good'];
    document.getElementById('good-pct').textContent = 
        `${(counts['Good']/total*100).toFixed(1)}%`;
    
    document.getElementById('fair-count').textContent = counts['Fair'];
    document.getElementById('fair-pct').textContent = 
        `${(counts['Fair']/total*100).toFixed(1)}%`;
    
    document.getElementById('poor-count').textContent = counts['Poor'];
    document.getElementById('poor-pct').textContent = 
        `${(counts['Poor']/total*100).toFixed(1)}%`;
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
                    <strong>${product.name}</strong><br>
                    <small class="text-muted">Vendor: ${product.vendor_id}</small>
                </td>
                <td>
                    <span class="badge ${getQualityBadge(product.quality_level)}">
                        ${product.quality_level}
                    </span>
                </td>
                <td>
                    <strong>${product.quality_score}</strong>/100
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