# Kayak Flight Scraper with Nearby Ariports

A Python tool that finds the cheapest flight combinations from Kayak by searching multiple nearby airports and dates.

## Features

- Searches for flights from multiple nearby airports within a specified radius
- Compares prices across a range of departure and return dates
- Finds direct flights (no layovers) for the most convenient travel
- Returns comprehensive pricing information for all possible combinations

## Requirements

- Python 3.6+
- Chrome browser
- ChromeDriver (compatible with your Chrome version)

## Installation

1. Clone this repository
2. Install dependencies using one of these methods:
   
   **Option 1: Using requirements.txt (recommended)**
   ```
   pip install -r requirements.txt
   ```
   
   **Option 2: Manual installation**
   ```
   pip install pandas selenium
   ```
3. Make sure you have the `airports.csv` file in the same directory as the script

## Requirements.txt

The project includes a `requirements.txt` file with all necessary dependencies:

```
pandas==2.0.0
selenium==4.10.0
```

You can update these versions as needed or install specific versions for compatibility.

## Usage

Edit the parameters in the `main()` function of `flight_scraper.py`:

```python
from_ = "MUC"               # Origin airport code
to_ = "HAM"                 # Destination airport code  
input_date = "2025-04-01"   # Target departure date
plus_minus_days = 2         # Days to check before/after target date
needed_days = 4             # Length of stay
near_airport_threshold_km = 300  # Max distance to look for alternative airports
```

Additional options:
```python
# Whether to only consider nearby airports in the same country
DEPARTURE_START_SAME_COUNTRY = True
DEPARTURE_END_SAME_COUNTRY = True
RETURN_START_SAME_COUNTRY = True
RETURN_END_SAME_COUNTRY = True
```

Run the script:
```
python flight_scraper.py
```

## How It Works

1. The script calculates all dates to check based on the target date and plus/minus range
2. It identifies nearby airports within the specified radius using the haversine formula
3. For each combination of dates and airports, it scrapes Kayak for the cheapest direct flight
4. Results are displayed showing departure and return flight details with prices

## Limitations

- Only searches for direct flights (no layovers)
- Prices are in Turkish Lira (TL) as the script uses Kayak's Turkish site
- Designed for student tickets (can be modified in the URL)
- Requires stable internet connection for web scraping
