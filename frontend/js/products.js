// Products List JavaScript - FIXED

let allProducts = [];
let filteredProducts = [];
let currentPage = 1;
const itemsPerPage = 20;

async function loadProducts() {
    try {
        const response = await fetch('/data/output/normalized_products.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        allProducts = await response.json();
        filteredProducts = allProducts;
        
        populateCategoryFilter();
        displayProducts();
    } catch (error) {
        console.error('Error loading products:', error);
        document.getElementById('productsTable').innerHTML = `
            <tr><td colspan="7" class="text-center text-danger">
                Error loading products: ${error.message}<br>
                <small>Please ensure the pipeline has been run and data files exist.</small>
            </td></tr>
        `;
    }
}

function populateCategoryFilter() {
    const categories = [...new Set(allProducts.map(p => p.category))].filter(c => c).sort();
    const select = document.getElementById('categoryFilter');
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat;
        select.appendChild(option);
    });
}

function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const vendor = document.getElementById('vendorFilter').value;
    const category = document.getElementById('categoryFilter').value;
    
    filteredProducts = allProducts.filter(product => {
        const matchesSearch = !searchTerm || 
            product.name.toLowerCase().includes(searchTerm) ||
            (product.brand_normalized || '').toLowerCase().includes(searchTerm);
        const matchesVendor = !vendor || product.vendor_id === vendor;
        const matchesCategory = !category || product.category === category;
        
        return matchesSearch && matchesVendor && matchesCategory;
    });
    
    currentPage = 1;
    displayProducts();
}

function displayProducts() {
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageProducts = filteredProducts.slice(start, end);
    
    const tbody = document.getElementById('productsTable');
    tbody.innerHTML = pageProducts.map(product => {
        // Handle price - could be number or string
        const price = typeof product.price === 'number' ? product.price : parseFloat(product.price) || 0;
        const priceDisplay = price.toFixed(2);
        
        return `
            <tr>
                <td><small class="text-muted">${product.id.substring(0, 8)}...</small></td>
                <td><span class="badge bg-primary">${product.vendor_id}</span></td>
                <td>${product.name}</td>
                <td>${product.brand_normalized || '-'}</td>
                <td>${product.category || '-'}</td>
                <td><strong>${product.currency || 'USD'} ${priceDisplay}</strong></td>
                <td>
                    ${product.image_status === 'valid' 
                        ? '<i class="bi bi-check-circle-fill text-success"></i>' 
                        : '<i class="bi bi-x-circle-fill text-danger"></i>'}
                </td>
            </tr>
        `;
    }).join('');
    
    updatePagination();
    document.getElementById('productCount').textContent = `${filteredProducts.length} products`;
}

function updatePagination() {
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">Previous</a>
        </li>
    `;
    
    // Page numbers (show max 5 pages)
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${currentPage === i ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    // Next button
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">Next</a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

function changePage(page) {
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        displayProducts();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    return false;
}

// Initialize
document.addEventListener('DOMContentLoaded', loadProducts);