// Products List JavaScript

let allProducts = [];
let filteredProducts = [];
let currentPage = 1;
const itemsPerPage = 20;

async function loadProducts() {
    try {
        const response = await fetch('../data/output/normalized_products.json');
        allProducts = await response.json();
        filteredProducts = allProducts;
        
        populateCategoryFilter();
        displayProducts();
    } catch (error) {
        document.getElementById('productsTable').innerHTML = `
            <tr><td colspan="7" class="text-center text-danger">
                Error loading products. Please run the pipeline first.
            </td></tr>
        `;
    }
}

function populateCategoryFilter() {
    const categories = [...new Set(allProducts.map(p => p.category))].sort();
    const select = document.getElementById('categoryFilter');
    categories.forEach(cat => {
        if (cat) {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            select.appendChild(option);
        }
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
    tbody.innerHTML = pageProducts.map(product => `
        <tr>
            <td><small class="text-muted">${product.id.substring(0, 8)}...</small></td>
            <td><span class="badge bg-primary">${product.vendor_id}</span></td>
            <td>${product.name}</td>
            <td>${product.brand_normalized || '-'}</td>
            <td>${product.category || '-'}</td>
            <td><strong>${product.currency} ${product.price.toFixed(2)}</strong></td>
            <td>
                ${product.image_status === 'valid' 
                    ? '<i class="bi bi-check-circle-fill text-success"></i>' 
                    : '<i class="bi bi-x-circle-fill text-danger"></i>'}
            </td>
        </tr>
    `).join('');
    
    updatePagination();
    document.getElementById('productCount').textContent = `${filteredProducts.length} products`;
}

function updatePagination() {
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
    const pagination = document.getElementById('pagination');
    
    let html = '';
    
    // Previous button
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">Previous</a>
        </li>
    `;
    
    // Page numbers
    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
        html += `
            <li class="page-item ${currentPage === i ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    // Next button
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">Next</a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

function changePage(page) {
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        displayProducts();
        window.scrollTo(0, 0);
    }
    return false;
}

// Initialize
document.addEventListener('DOMContentLoaded', loadProducts);