# Building Clustering Application

This application provides a graphical interface for clustering buildings based on their geographical location, taking into account their position relative to a river.

## Features

- Select multiple streets for analysis
- Automatic clustering of buildings using DBSCAN algorithm
- Separate clustering for buildings on different sides of the river
- Export results to CSV file

## Requirements

- Python 3.x
- pandas
- numpy
- matplotlib
- scikit-learn
- geopandas
- tkinter

## Installation

1. Clone the repository
2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the interface:
```bash
python interface.py
```

2. Select streets using either:
   - Single street selection from dropdown
   - Multiple street selection using the dedicated button

3. Click "Кластеризовать здания" to perform clustering

4. Results will be saved to `clustered_buildings.csv`

## Data Format

The application expects:
- An Excel file (`data2.xlsx`) with building data
- A GeoJSON file (`riverMAin.json`) with river geometry
