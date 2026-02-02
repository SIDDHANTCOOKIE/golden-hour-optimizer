import osmnx as ox
from sklearn.cluster import KMeans
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import sys

def main():
    print("Initialize Golden Hour Optimizer...")
    
    # 1. GET REAL DATA: Download street network for a specific area
    # Check if a location was provided via command line, otherwise default
    if len(sys.argv) > 1:
        # Join arguments in case of spaces, e.g., "New York, USA"
        place_name = " ".join(sys.argv[1:])
    else:
        place_name = 'Koramangala, Bengaluru'
        print("No location argument provided. Using default: 'Koramangala, Bengaluru'")
        print("Usage: python main.py <Location Name>")

    print(f"Downloading street network for: {place_name}...")
    try:
        G = ox.graph_from_place(place_name, network_type='drive')
    except Exception as e:
        print(f"Warning: graph_from_place failed ({e}). Attempting graph_from_point...")
        try:
            # Fallback: Get coordinates for the place and download graph around it
            # Using geocoder to get lat,lon
            location = ox.geocode(place_name)
            G = ox.graph_from_point(location, dist=2000, network_type='drive')
            print("Successfully downloaded point-based graph.")
        except Exception as e2:
            print(f"Error downloading data: {e2}")
            return

    # Convert graph to GeoDataFrames
    nodes, edges = ox.graph_to_gdfs(G)
    
    print(f"Graph loaded with {len(nodes)} nodes and {len(edges)} edges.")

    # 2. MODEL RISK: Filter for busy intersections (nodes with many street connections)
    # 'street_count' is a real attribute from OpenStreetMap
    print("Modeling risk based on intersection complexity...")
    
    # Ensure street_count is present
    if 'street_count' not in nodes.columns:
        print("Calculating street count...")
        # basic approximation if not present (though ox usually provides it)
        street_count = nodes.index.map(lambda n: G.degree(n))
        nodes['street_count'] = street_count

    # Filter high risk nodes (>= 4 connections)
    high_risk_nodes = nodes[nodes['street_count'] >= 4].copy()
    
    if len(high_risk_nodes) < 5:
        print("Not enough high risk nodes found with >= 4 connections. Lowering threshold to 3.")
        high_risk_nodes = nodes[nodes['street_count'] >= 3].copy()

    print(f"Identified {len(high_risk_nodes)} high-risk intersections.")
    
    # Get coordinates for clustering (Lat/Long)
    # OSMnx nodes usually have 'y' (lat) and 'x' (lon)
    coords = high_risk_nodes[['y', 'x']].values

    # 3. OPTIMIZE: Find 5 best 'Standby Points' using K-Means
    print("Optimizing ambulance standby locations using K-Means...")
    
    n_ambulances = 5
    kmeans = KMeans(n_clusters=n_ambulances, random_state=42, n_init=10).fit(coords)
    optimal_locations = kmeans.cluster_centers_

    print("Optimal Ambulance Locations (Lat, Lon):")
    for i, loc in enumerate(optimal_locations):
        print(f"  Hub {i+1}: {loc[0]:.6f}, {loc[1]:.6f}")

    # 4. VISUALIZE: Plot the map with new optimal ambulance spots
    print("Generating visualization...")
    fig, ax = ox.plot_graph(G, show=False, close=False, edge_color='#999999', edge_linewidth=0.5, node_size=0)
    
    # Plot high risk nodes (optional, small blue dots)
    ax.scatter(coords[:, 1], coords[:, 0], c='blue', s=10, alpha=0.5, label='High Risk Intersections', zorder=2)
    
    # Plot optimal hubs (large red dots)
    # Note: matplotlib scatter takes (x, y) which corresponds to (lon, lat)
    ax.scatter(optimal_locations[:, 1], optimal_locations[:, 0], c='red', s=150, marker='*', label='Optimized Ambulance Hubs', zorder=3)
    
    plt.title(f"Golden Hour Optimizer: {place_name}\nOptimal Ambulance Standby Points", fontsize=14)
    plt.legend()
    
    # Save the figure
    output_file = 'ambulance_optimization_map.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Map saved to {output_file}")
    
    # Show plot if interactive
    # plt.show()

if __name__ == "__main__":
    main()
