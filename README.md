# Heat Pump Efficacy Dashboard

## Overview

This project is an interactive dashboard designed to help users evaluate whether installing a heat pump is a good choice based on weather data from a specific location in the United States. Heat pumps are energy-efficient alternatives to traditional gas furnaces but may perform less effectively in extremely cold temperatures. The dashboard allows users to explore historical weather data to understand how a heat pump might function in their area.

## Features

- **Interactive Map**: Input your city and state to see weather data and a pinpoint location on a map.
- **Weather Analysis**: View historical temperature data to assess heat pump efficiency.
- **Temperature Settings**: Choose between Fahrenheit and Celsius and set temperature thresholds.
- **Rolling Averages**: Option to include weekly or monthly rolling averages for a smoother data view.

## Getting Started

### Prerequisites

Ensure you have Python installed. You can install the required dependencies with:

```bash
pip install -r requirements.txt
```

### Running the Dashboard

To run the dashboard, use the following command:

```bash
shiny run app.py
```

### Repository Structure

Your completed project should follow this directory structure:

```kotlin
./heatpump-dashboard/
│
├── data/
│   └── cities.csv
├── data-raw/
│   └── uscities.csv
├── .gitignore
├── README.md
├── app.py
├── process-data.py
└── requirements.txt
```

- **data/**: Processed city and state data.
- **data-raw/**: Raw location data before processing.
- **app.py**: The main application file for the dashboard.
- **process-data.py**: Script to process raw data into usable format.
- **requirements.txt**: Lists the required Python packages.
- **.gitignore**: Specifies files and directories to be ignored by Git.

## How to Use

1. **Select a Location**: Enter a city and state to get started.
2. **Choose Date Range**: Pick a date range to view historical weather data.
3. **Adjust Temperature Settings**: Set your preferred temperature unit and thresholds.
4. **Explore the Data**: Use the interactive map, view rolling averages, and analyze the data to decide if a heat pump is suitable for your location.

## Data Sources

- **Weather Data**: Retrieved from the Open-Meteo Historical Weather API.
- **Location Data**: Sourced from SimpleMaps, processed to include cities with populations over 10,000.

## Technology Stack

- **Dashboard Framework**: Shiny for Python, enabling interactive and reactive elements in the user interface.
- **Data Manipulation**: Pandas for processing and handling weather data.
- **Visualization**: Matplotlib, Seaborn, or Plotnine for creating static plots, with optional use of ipywidgets and ipyleaflet for map interactivity.
