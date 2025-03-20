import math, time
import pandas as pd
from selenium import webdriver
from typing import List, Tuple
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the Earth (specified in decimal degrees) using the Haversine formula.
    """
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    # Radius of Earth in kilometers. Use 6371 for km.
    km = 6371 * c
    return km

def near_airports(airport_code, destination_airport,km,same_country=False):
    # Get the coordinates of the airport based on the airport code from airports.csv's "code", "latitude", and "longitude" columns
    # Read airports.csv
    df = pd.read_csv('airports.csv')
    
    # Find the row with matching airport code and get coordinates
    airport_row = df[df['code'] == airport_code]
    if len(airport_row) == 0:
        return None
        
    latitude = float(airport_row['latitude'].iloc[0])
    longitude = float(airport_row['longitude'].iloc[0])
    
    near_airports = [airport_code]

    # Calculate the distance between the airport and all other airports
    for index, row in df.iterrows():
        if row['code'] == airport_code or row['code'] == destination_airport or (same_country and row['country'] != airport_row['country'].iloc[0]) :
            continue

        near_airport_code = row['code']
        distance = haversine(longitude, latitude, row['longitude'], row['latitude'])
        if distance < km:
            near_airports.append(near_airport_code)

    print(f"Airports near {airport_code} are {near_airports}, total of {len(near_airports)} airports.\n")
    return near_airports

class FlightScraper:
    def __init__(self):
        # Set up Chrome options for the webdriver
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--log-level=3')  # Suppress console logging
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])  # Disable automation logging
        chrome_options.add_experimental_option('useAutomationExtension', False)  # Disable automation extension
        chrome_options.add_argument('--silent')  # Suppress console output
        chrome_options.add_argument('--headless=new')  # Run in headless mode
        chrome_options.add_argument('--disable-gpu')  # Required for headless mode
        chrome_options.add_argument('--disable-web-security')  # Disable web security
        chrome_options.add_argument('--disable-webgl')  # Disable WebGL
        chrome_options.add_argument('--disable-software-rasterizer')  # Disable software rasterizer
        chrome_options.add_argument('--window-size=1920,1080')  # Set window size
        chrome_options.add_argument('--start-maximized')  # Start maximized
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # Disable automation flag
        chrome_options.add_argument('--disable-extensions')  # Disable extensions
        chrome_options.add_argument('--disable-infobars')  # Disable infobars
        chrome_options.add_argument('--ignore-certificate-errors')  # Ignore certificate errors
        self.options = chrome_options

    def scrape_cheapest_flight_price(self, from_: str, to_: str, departure_date: str) -> int:
        """Internal method to scrape price (runs in thread pool)"""
        driver = webdriver.Chrome(options=self.options)
        try:
            url = f"https://www.kayak.com.tr/flights/{from_}-{to_}/{departure_date}/1students?&sort=price_a&fs=stops=~0"
            driver.get(url)
            
            # Wait for cookie button to be present and click it
            cookie_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'RxNS-button-content') and text()='Tümünü reddet']"))
            )
            cookie_button.click()
            
            # Wait 2 seconds after clicking the cookie button
            time.sleep(2)
            
            # Original wait of 3 seconds
            time.sleep(3)
            
            # Wait for the first valid result item to be present (excluding ones with JW4C class)
            result_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'Fxw9-result-item-container') and not(.//div[contains(@class, 'JW4C')])]"))
            )
            
            try:
                # Find the price element within the container
                price_element = result_container.find_element(By.CLASS_NAME, "f8F1-price-text")
                price_text = price_element.text
                
                # Extract just the numeric value from the price
                price = ''.join(filter(str.isdigit, price_text))
                return int(price)
            except Exception as e:
                print(f"No flights found or price could not be extracted: {str(e)}")
                return None
            finally:
                driver.quit()
        except Exception as e:
            print(f"Error scraping flight data: {str(e)}")
            return None
        finally:
            driver.quit()

    def get_flights(self, departure_dates: List[str], near_departure_start_airports: List[str], near_departure_end_airports: List[str]) -> List[Tuple[str, str, str, int]]:
        """Get flights asynchronously for multiple routes and dates."""
        flights = []
        # Create tasks for all combinations
        for departure_date in departure_dates:
            for departure_start_airport in near_departure_start_airports:
                for departure_end_airport in near_departure_end_airports:
                    if departure_start_airport != departure_end_airport:
                        price = self.scrape_cheapest_flight_price(departure_start_airport, departure_end_airport, departure_date)
                        if price is not None:
                            flights.append((departure_start_airport, departure_end_airport, departure_date, price))
        
        return flights

def main():
    scraper = FlightScraper()
    try:

        from_ = "MUC"
        to_ = "HAM"
        input_date = "2025-04-01"
        plus_minus_days = 2
        needed_days = 4
        near_airport_threshold_km = 300

        DEPARTURE_START_SAME_COUNTRY = True
        DEPARTURE_END_SAME_COUNTRY = True
        RETURN_START_SAME_COUNTRY = True
        RETURN_END_SAME_COUNTRY = True
        
        departure_dates = [(datetime.strptime(input_date, "%Y-%m-%d") + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(-plus_minus_days-1, plus_minus_days + 1)]
        return_dates = [(datetime.strptime(departure_date, "%Y-%m-%d") + timedelta(days=needed_days)).strftime("%Y-%m-%d") for departure_date in departure_dates]
        
        near_departure_start_airports = near_airports(from_, to_, near_airport_threshold_km, DEPARTURE_START_SAME_COUNTRY)
        near_departure_end_airports = near_airports(to_, from_, near_airport_threshold_km, DEPARTURE_END_SAME_COUNTRY)

        # Get departure flights asynchronously
        departure_flights = scraper.get_flights(departure_dates, near_departure_start_airports, near_departure_end_airports)

        near_return_start_airports = near_airports(from_, to_, near_airport_threshold_km, RETURN_START_SAME_COUNTRY)
        near_return_end_airports = near_airports(to_, from_, near_airport_threshold_km, RETURN_END_SAME_COUNTRY)

        # Get return flights asynchronously
        return_flights = scraper.get_flights(return_dates, near_return_start_airports, near_return_end_airports)

        # Print all options with dates and prices
        for departure_flight, return_flight in zip(departure_flights, return_flights):
            print(f"Departure: {departure_flight[0]} to {departure_flight[1]} on {departure_flight[2]} costs {departure_flight[3]} TL.")
            print(f"Return: {return_flight[0]} to {return_flight[1]} on {return_flight[2]} costs {return_flight[3]} TL.")
            print(f"Total cost: {departure_flight[3] + return_flight[3]} TL.\n")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 