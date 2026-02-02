# The "Golden Hour" Optimizer (Facility Location Problem)

## 🏥 Validating the Need
In Indian cities, ambulances are usually stationed at hospitals. However, accidents often occur on highways and major junctions. The time lost navigating traffic to the accident site and back often exceeds the "Golden Hour"—the critical survival window.

## 🎯 Research Goal
To algorithmically determine the optimal standby locations for **5 ambulances** in a specific neighborhood (e.g., Koramangala, Bengaluru) to minimize average response time.

## ⚙️ How It Works ("The Real Implementation")
1.  **Data (OSMnx)**: Downloads the real driveable street network of the city sector from OpenStreetMap.
2.  **Modeling (Weighted Demand)**: Identifies "High Risk" nodes by filtering for busy intersections (nodes with high street counts).
3.  **Optimization (K-Means Clustering)**: Uses K-Means clustering algorithm on high-risk nodes to find mathematical "Centroids" for ambulance hubs.
4.  **Simulation & Visualization**: Plots current infrastructure vs. optimized probability-based locations.

## 🛠️ Usage

### Prerequisites
- Python 3.8+
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### Running the Optimizer
**Default (Koramangala):**
```bash
python main.py
```

**Custom Location:**
You can pass any city or neighborhood name as an argument:
```bash
python main.py "Indiranagar, Bengaluru"
```
```bash
python main.py "Manhattan, New York"
```

This will:
1.  Download map data for the specified location.
2.  Identify high-risk intersections.
3.  Calculate optimal ambulance locations.
4.  Generate a map `ambulance_optimization_map.png`.

### 🖥️ Interactive GUI
You can also run the web interface for an interactive experience:
```bash
streamlit run app.py
```
This opens a dashboard where you can slide to adjust the number of ambulances and see results on a zoomable map.

## 🧠 Why This Matters
This project solves a **Facility Location Problem** (a core Operations Research topic) using real GIS data. It moves beyond theoretical code to provide actionable policy recommendations for urban safety.
