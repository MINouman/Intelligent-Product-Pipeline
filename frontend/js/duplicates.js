// Duplicates JavaScript

let allGroups = [];
let enrichedProducts = {};

async function loadDuplicates() {
    try {
        const [groupsData, productsData] = await Promise.all([
            fetch('../data/output/duplicates.json').then(r => r.json()),
            fetch('../data/output/enriched_products.json').then(r => r.json())
        ]);
        
        allGroups = groupsData;
        
        // Create product lookup map
        productsData.forEach(p => {
            enrichedProducts[p.id] = p;
        });
        
        displayGroups(allGroups);
    } catch (error) {
        document.getElementById('duplicateGroups').innerHTML = `
            <div class="alert alert-warning">
                Error loading duplicates. Please run the pipeline first.
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
    
    container.innerHTML = groups.map((group, index) => {
        const products = group.products
            .map(id => enrichedProducts[id])
            .filter(p => p);
        
        return `
            <div class="card group-card mb-3">
                <div class="card-header bg-light">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            Group ${index + 1} 
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
                    <div class="table-responsive">
                        <table class="table table-sm mb-0">
                            <thead>
                                <tr>
                                    <th>Vendor</th>
                                    <th>Name</th>
                                    <th>Brand</th>
                                    <th>Price</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${products.map(p => `
                                    <tr>
                                        <td><span class="badge bg-primary">${p.vendor_id}</span></td>
                                        <td>${p.name}</td>
                                        <td>${p.brand_normalized || '-'}</td>
                                        <td>${p.currency} ${p.price.toFixed(2)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }).join('');
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