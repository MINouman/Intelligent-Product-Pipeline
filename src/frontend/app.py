"""
Rokomari AI Pipeline - Streamlit Dashboard

Complete UI for uploading messy data and running the pipeline.
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
from datetime import datetime
import io

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.normalizer import ProductNormalizer
from src.services.enricher import ProductEnricher
from src.services.duplicate_detector import DuplicateDetector
from src.services.product_validator import ProductValidator


st.set_page_config(
    page_title="Rokomari AI Pipeline",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'processed' not in st.session_state:
        st.session_state.processed = False
    if 'normalized_products' not in st.session_state:
        st.session_state.normalized_products = None
    if 'enriched_products' not in st.session_state:
        st.session_state.enriched_products = None
    if 'duplicates' not in st.session_state:
        st.session_state.duplicates = None
    if 'validated_products' not in st.session_state:
        st.session_state.validated_products = None
    if 'stats' not in st.session_state:
        st.session_state.stats = {}


def load_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.json'):
            data = json.loads(uploaded_file.getvalue().decode('utf-8'))
            return data if isinstance(data, list) else [data]
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            return df.to_dict('records')
        else:
            st.error("Unsupported file format. Please upload JSON or CSV.")
            return None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


def process_pipeline(products, threshold=0.60):
    normalizer = ProductNormalizer()
    enricher = ProductEnricher()
    detector = DuplicateDetector(similarity_threshold=threshold)
    validator = ProductValidator()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔄 Step 1/4: Normalizing products...")
        progress_bar.progress(10)
        normalized = normalizer.normalize_batch(products)
        norm_stats = normalizer.get_stats()
        progress_bar.progress(25)
        
        status_text.text("🔄 Step 2/4: Enriching with AI features...")
        progress_bar.progress(30)
        enriched = enricher.enrich_batch(normalized)
        progress_bar.progress(50)
        
        status_text.text("🔄 Step 3/4: Detecting duplicates...")
        progress_bar.progress(60)
        duplicates = detector.detect_duplicates(enriched)
        dup_stats = detector.get_stats()
        progress_bar.progress(75)
        
        status_text.text("🔄 Step 4/4: Validating quality...")
        progress_bar.progress(80)
        validated = validator.validate_batch(enriched)
        val_stats = validator.get_stats()
        progress_bar.progress(100)
        
        status_text.text("✅ Processing complete!")
        
        st.session_state.normalized_products = normalized
        st.session_state.enriched_products = enriched
        st.session_state.duplicates = duplicates
        st.session_state.validated_products = validated
        st.session_state.stats = {
            'normalization': norm_stats,
            'duplicates': dup_stats,
            'validation': val_stats
        }
        st.session_state.processed = True
        
        return True
        
    except Exception as e:
        st.error(f"Error during processing: {e}")
        progress_bar.progress(0)
        status_text.text("❌ Processing failed")
        return False


def display_overview():
    st.markdown('<p class="main-header">📊 Pipeline Results Overview</p>', unsafe_allow_html=True)
    
    if not st.session_state.processed:
        st.info("👈 Upload a file and click 'Process' to see results")
        return
    
    stats = st.session_state.stats

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Products",
            stats['normalization']['total_processed'],
            delta=None
        )
    
    with col2:
        success_rate = stats['normalization']['success_rate']
        st.metric(
            "Normalization Success",
            f"{success_rate:.1f}%",
            delta=f"{success_rate - 80:.1f}% vs target" if success_rate >= 80 else None
        )
    
    with col3:
        dup_rate = (len(st.session_state.duplicates) / 
                   stats['normalization']['total_processed'] * 100)
        st.metric(
            "Duplicate Groups",
            len(st.session_state.duplicates),
            delta=f"{dup_rate:.1f}% of products"
        )
    
    with col4:
        excellent_pct = stats['validation']['excellent_pct']
        st.metric(
            "Excellent Quality",
            f"{excellent_pct:.1f}%",
            delta=None
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        quality_data = {
            'Quality Level': ['Excellent', 'Good', 'Fair', 'Poor'],
            'Count': [
                stats['validation']['excellent'],
                stats['validation']['good'],
                stats['validation']['fair'],
                stats['validation']['poor']
            ]
        }
        fig = px.bar(
            quality_data,
            x='Quality Level',
            y='Count',
            title='Product Quality Distribution',
            color='Quality Level',
            color_discrete_map={
                'Excellent': '#28a745',
                'Good': '#17a2b8',
                'Fair': '#ffc107',
                'Poor': '#dc3545'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        method_data = stats['duplicates']['method_breakdown']
        if method_data:
            fig = px.pie(
                values=list(method_data.values()),
                names=list(method_data.keys()),
                title='Duplicate Detection Methods'
            )
            st.plotly_chart(fig, use_container_width=True)


def display_products():
    st.header("📦 Processed Products")
    
    if not st.session_state.processed:
        st.info("No products to display. Upload and process data first.")
        return
    
    products = st.session_state.validated_products

    col1, col2, col3 = st.columns(3)
    
    with col1:
        quality_filter = st.multiselect(
            "Filter by Quality",
            ['Excellent', 'Good', 'Fair', 'Poor'],
            default=['Excellent', 'Good']
        )
    
    with col2:
        vendors = list(set(p.get('vendor_id', 'Unknown') for p in products))
        vendor_filter = st.multiselect(
            "Filter by Vendor",
            vendors,
            default=vendors
        )
    
    with col3:
        search_term = st.text_input("Search products", "")
    
    filtered = products
    if quality_filter:
        filtered = [p for p in filtered if p.get('quality_level') in quality_filter]
    if vendor_filter:
        filtered = [p for p in filtered if p.get('vendor_id') in vendor_filter]
    if search_term:
        filtered = [p for p in filtered 
                   if search_term.lower() in p.get('name', '').lower()]
    
    st.write(f"Showing {len(filtered)} of {len(products)} products")
    
    df = pd.DataFrame([
        {
            'ID': p.get('id', '')[:8] + '...',
            'Vendor': p.get('vendor_id', ''),
            'Name': p.get('name', ''),
            'Brand': p.get('brand_normalized', ''),
            'Category': p.get('category', ''),
            'Price': f"{p.get('currency', '')} {p.get('price', 0):.2f}",
            'Quality': p.get('quality_level', ''),
            'Score': p.get('quality_score', 0)
        }
        for p in filtered[:100]  
    ])
    
    st.dataframe(df, use_container_width=True, height=400)
    
    if st.button("📥 Export Filtered Products"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


def display_duplicates():
    st.header("🔍 Duplicate Detection Results")
    
    if not st.session_state.processed:
        st.info("No duplicates to display. Upload and process data first.")
        return
    
    duplicates = st.session_state.duplicates
    
    st.write(f"Found **{len(duplicates)}** duplicate groups")
    
    duplicates_sorted = sorted(duplicates, key=lambda x: x['group_size'], reverse=True)

    for i, group in enumerate(duplicates_sorted[:10], 1):
        with st.expander(
            f"Group {i}: {group['group_size']} products "
            f"(Confidence: {group['confidence']:.2f}, Method: {group['method']})"
        ):
            products_in_group = [
                p for p in st.session_state.enriched_products 
                if p['id'] in group['products']
            ]
            
            for product in products_in_group:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{product['name']}**")
                    st.write(f"Vendor: {product['vendor_id']} | "
                            f"Brand: {product.get('brand_normalized', 'N/A')} | "
                            f"Price: {product.get('currency', '')} {product.get('price', 0):.2f}")
                with col2:
                    if product.get('image_url'):
                        st.write(f"[View Image]({product['image_url']})")
                st.markdown("---")


def main():
    initialize_session_state()
    
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/1f77b4/ffffff?text=Rokomari+AI", 
                use_column_width=True)
        st.title("🚀 AI Pipeline")
        st.markdown("---")
        
        st.subheader("📤 Upload Data")
        uploaded_file = st.file_uploader(
            "Upload messy products (JSON or CSV)",
            type=['json', 'csv'],
            help="Upload a JSON array or CSV file with product data"
        )
        
        st.subheader("⚙️ Configuration")
        threshold = st.slider(
            "Duplicate Detection Threshold",
            min_value=0.5,
            max_value=0.9,
            value=0.60,
            step=0.05,
            help="Higher = stricter matching (fewer duplicates)"
        )
        
        if uploaded_file is not None:
            if st.button("🚀 Process Pipeline", type="primary", use_container_width=True):
                products = load_uploaded_file(uploaded_file)
                if products:
                    st.info(f"Loaded {len(products)} products")
                    with st.spinner("Processing..."):
                        success = process_pipeline(products, threshold)
                    if success:
                        st.success("✅ Processing complete!")
                        st.balloons()
        
        st.markdown("---")
        
        st.subheader("📑 Navigation")
        page = st.radio(
            "Select page:",
            ["Overview", "Products", "Duplicates"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.session_state.processed:
            st.subheader("📊 Quick Stats")
            stats = st.session_state.stats
            st.metric("Success Rate", f"{stats['normalization']['success_rate']:.1f}%")
            st.metric("Duplicate Groups", len(st.session_state.duplicates))
            st.metric("Excellent Quality", f"{stats['validation']['excellent_pct']:.1f}%")
    
    # Main content
    if page == "Overview":
        display_overview()
    elif page == "Products":
        display_products()
    elif page == "Duplicates":
        display_duplicates()


if __name__ == "__main__":
    main()