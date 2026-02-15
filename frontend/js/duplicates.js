// Duplicates JavaScript - FIXED with expanded product details

let allGroups = [];
let enrichedProducts = {};

async function loadDuplicates() {
    try {
        const [groupsData, productsData] = await Promise.all([
            fetch('/data/output/duplicates.json').then(r => {
                if (!r.ok) throw new Error(`Duplicates: HTTP ${r.status}`);
                return r.json();
            }),
            fetch('/data/output/enriched_products.json').then(r => {
                if (!r.ok) throw new Error(`Products: HTTP ${r.status}`);
                return r.json();
            })
        ]);
        
        allGroups = groupsData;
        
        // Create product lookup map
        productsData.forEach(p => {
            enrichedProducts[p.id] = p;
        });
        
        displayGroups(allGroups);
    } catch (error) {
        console.error('Error loading duplicates:', error);
        document.getElementById('duplicateGroups').innerHTML = `
            <div class="alert alert-warning">
                Error loading duplicates: ${error.message}<br>
                <small>Please ensure the pipeline has been run first.</small>
            </div>
        `;
    }
}

function applyFilters() {
    const method = document.getElementById('methodFilter').value;
    const size = parseInt(document.getElementById('sizeFilter').value) || 0;
    const confidence = parseInt(document.getElementById('confidenceFilter').value) / 100;
    
    document.getElementById('confValue').textContent = 
        (confidence * 100).toFixed(0);
    
    const filtered = allGroups.filter(group => {
        const matchesMethod = !method || group.method === method;
        const matchesSize = size === 0 || group.group_size >= size;
        const matchesConfidence = group.confidence >= confidence;
        
        return matchesMethod && matchesSize && matchesConfidence;
    });
    
    displayGroups(filtered);
}

function displayGroups(groups) {
    const container = document.getElementById('duplicateGroups');
    document.getElementById('groupCount').textContent = `${groups.length} groups`;
    
    if (groups.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                No duplicate groups match your filters.
            </div>
        `;
        return;
    }
    
    container.innerHTML = groups.slice(0, 50).map((group, index) => {
        const products = group.products
            .map(id => enrichedProducts[id])
            .filter(p => p);
        
        if (products.length === 0) {
            return '';
        }
        
        return `
            <div class="card group-card mb-3">
                <div class="card-header bg-light">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="bi bi-diagram-3"></i> Group ${index + 1} 
                            <span class="badge bg-secondary">${group.group_size} products</span>
                        </h6>
                        <div>
                            <span class="badge ${getMethodColor(group.method)} method-badge">
                                ${group.method}
                            </span>
                            <span class="badge bg-info method-badge">
                                ${(group.confidence * 100).toFixed(0)}% confidence
                            </span>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        ${products.map(p => {
                            const price = typeof p.price === 'number' ? p.price : parseFloat(p.price) || 0;
                            return `
                                <div class="col-md-6">
                                    <div class="card h-100">
                                        <div class="card-body">
                                            <div class="d-flex justify-content-between align-items-start mb-2">
                                                <span class="badge bg-primary">${p.vendor_id}</span>
                                                <small class="text-muted">${p.id.substring(0, 8)}...</small>
                                            </div>
                                            <h6 class="card-title">${p.name}</h6>
                                            <div class="small">
                                                <p class="mb-1">
                                                    <strong>Brand:</strong> ${p.brand_normalized || 'N/A'}
                                                </p>
                                                <p class="mb-1">
                                                    <strong>Category:</strong> ${p.category || 'N/A'}
                                                </p>
                                                <p class="mb-1">
                                                    <strong>Price:</strong> 
                                                    <span class="text-success fw-bold">
                                                        ${p.currency || 'USD'} ${price.toFixed(2)}
                                                    </span>
                                                </p>
                                                <p class="mb-0">
                                                    <strong>Image:</strong> 
                                                    ${p.image_status === 'valid' 
                                                        ? '<i class="bi bi-check-circle-fill text-success"></i> Valid' 
                                                        : '<i class="bi bi-x-circle-fill text-danger"></i> Invalid'}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    if (groups.length > 50) {
        container.innerHTML += `
            <div class="alert alert-info mt-3">
                Showing first 50 of ${groups.length} groups. Use filters to narrow results.
            </div>
        `;
    }
}

function getMethodColor(method) {
    const colors = {
        'embedding': 'bg-primary',
        'hybrid': 'bg-success',
        'fuzzy': 'bg-warning',
        'rule_based': 'bg-danger',
        'none': 'bg-secondary'
    };
    return colors[method] || 'bg-secondary';
}

document.addEventListener('DOMContentLoaded', loadDuplicates);