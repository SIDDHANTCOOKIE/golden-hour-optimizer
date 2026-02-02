import streamlit as st
import osmnx as ox
from sklearn.cluster import KMeans
import folium
from streamlit_folium import st_folium
import numpy as np

# Set page configuration
st.set_page_config(page_title="Golden Hour Optimizer", page_icon="🚑", layout="wide")

st.title("🚑 Golden Hour Optimizer")
st.markdown("""
This tool uses **Operations Research (Facility Location Problem)** to find the optimal standby locations for ambulances.
It downloads real street network data, identifies high-risk intersections, and uses **K-Means Clustering** to position ambulances.
""")

# Sidebar for controls
st.sidebar.header("Configuration")

# Mode Selection
optimization_mode = st.sidebar.radio("Optimization Mode", ["City / Neighborhood", "Highway Route (Demo)"])

if optimization_mode == "City / Neighborhood":
    place_name = st.sidebar.text_input("📍 Location Name", value="Koramangala, Bengaluru", help="Enter a city or neighborhood")
    dist_val = 2000 # Default search radius
elif optimization_mode == "Highway Route (Demo)":
    # Preset for Delhi-Mumbai Expressway (Sohna-Dausa stretch approximation or Vadodara)
    # Using a coordinate point on the expressway near Sohna for reliable graph download
    st.sidebar.info("🛣️ Optimizing a 10km stretch of the Delhi-Mumbai Expressway (near Sohna).")
    place_name = "Delhi-Mumbai Expressway (Sohna Segment)"
    # Coordinates for Sohna start of DME: ~28.2378, 77.0697
    highway_center = (28.2378, 77.0697) 
    dist_val = 5000 # 5km radius = 10km stretch

n_ambulances = st.sidebar.slider("Number of Ambulances", min_value=1, max_value=20, value=5)
risk_threshold = st.sidebar.slider("Minimum Intersections (Risk Threshold)", min_value=3, max_value=6, value=3 if optimization_mode == "Highway Route (Demo)" else 4, help="Lower threshold for highways as junctions are fewer.")

def get_data_and_optimize(mode, place, center_point, dist, n_clusters, threshold):
    with st.spinner(f"Downloading network data for {place}..."):
        try:
            if mode == "Highway Route (Demo)":
                # Download network around the specific highway point
                G = ox.graph_from_point(center_point, dist=dist, network_type='drive')
            else:
                # Default City Mode
                try:
                    G = ox.graph_from_place(place, network_type='drive')
                except:
                     # Fallback to point-based
                    location = ox.geocode(place)
                    G = ox.graph_from_point(location, dist=dist, network_type='drive')
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return None, None, None

    with st.spinner("Analyzing high-risk points..."):
        nodes, edges = ox.graph_to_gdfs(G)
        
        # Calculate street count if missing
        if 'street_count' not in nodes.columns:
            street_count = nodes.index.map(lambda n: G.degree(n))
            nodes['street_count'] = street_count

        # Filter high risk nodes
        high_risk_nodes = nodes[nodes['street_count'] >= threshold].copy()
        
        # If very few risk nodes (common on highways), use random sampling or lower threshold
        if len(high_risk_nodes) < n_clusters:
            st.warning(f"Few high-connectivity nodes found ({len(high_risk_nodes)}). Including medium-risk nodes.")
            high_risk_nodes = nodes[nodes['street_count'] >= 2].copy()

        if len(high_risk_nodes) < n_clusters:
             coords = nodes[['y', 'x']].values
        else:
            coords = high_risk_nodes[['y', 'x']].values

    with st.spinner("Calculating optimal ambulance positions..."):
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit(coords)
        optimal_locations = kmeans.cluster_centers_

    return G, high_risk_nodes, optimal_locations

# Main Execution Trigger
if st.sidebar.button("🚀 Optimize Locations", type="primary"):
    # Determine center point for function call (None if city mode, as it geocodes by name)
    center = highway_center if optimization_mode == "Highway Route (Demo)" else None
    
    G, risk_nodes, opt_locs = get_data_and_optimize(optimization_mode, place_name, center, dist_val, n_ambulances, risk_threshold)
    
    if G is not None:
        # Save to session state to preventing resetting
        st.session_state['G'] = G
        st.session_state['risk_nodes'] = risk_nodes
        st.session_state['opt_locs'] = opt_locs
        st.session_state['data_loaded'] = True
        st.session_state['current_place'] = place_name
    else:
        st.session_state['data_loaded'] = False

# Display logic based on session state
if st.session_state.get('data_loaded', False):
    st.subheader(f"Results for: {st.session_state.get('current_place', 'Unknown')}")
    
    G = st.session_state['G']
    risk_nodes = st.session_state['risk_nodes']
    opt_locs = st.session_state['opt_locs']

    # Create Folium Map
    center_lat, center_lon = opt_locs[0][0], opt_locs[0][1]
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13 if optimization_mode == "Highway Route (Demo)" else 14, tiles="CartoDB positron")

    # Add High Risk Nodes
    if not risk_nodes.empty:
        for idx, row in risk_nodes.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=3,
                color="blue",
                fill=True,
                fill_opacity=0.5,
                popup="High Risk Point"
            ).add_to(m)

    # Add Optimal Ambulance Hubs
    for i, loc in enumerate(opt_locs):
        folium.Marker(
            location=[loc[0], loc[1]],
            popup=f"🚑 Hub #{i+1}",
            icon=folium.Icon(color="red", icon="ambulance", prefix="fa")
        ).add_to(m)

    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Network Size (Nodes)", len(G.nodes))
    c2.metric("High Risk Zones", len(risk_nodes))
    c3.metric("Ambulances Deployed", len(opt_locs))

    st_folium(m, width="100%", height=600)
    
    # Coordinates Table
    st.caption("Copy optimal coordinates for deployment:")
    st.code("\n".join([f"Unit {i+1}: {loc[0]:.6f}, {loc[1]:.6f}" for i, loc in enumerate(opt_locs)]))

elif "data_loaded" not in st.session_state:
    st.info("👈 Select a mode and click 'Optimize Locations' to start.")
