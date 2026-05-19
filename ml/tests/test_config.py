# import yaml

# with open("ml/config/cities.yaml") as f:
#     config = yaml.safe_load(f)

# cities = config["cities"]
# print(f"Cities loaded: {list(cities.keys())}")
# # Expected: ['abuja', 'lagos', 'kano', 'port_harcourt', 'ibadan', 'osogbo']

"""
# Discover real OpenAQ location IDs - test 2
from data_ingestion.openaq_fetcher import discover_cities, discover_locations

cities = discover_cities("NG")
print(f"OpenAQ localities in Nigeria: {len(cities)}")
for city in cities:
    print(city)

print("\nIbadan stations:")
locations = discover_locations("Ibadan", "NG")
for loc in locations:
    print(loc["id"], loc["name"], loc.get("locality"), loc.get("country", {}).get("code"))
"""


"""
# Fetch live weather
from data_ingestion.weather_fetcher import fetch_current_weather

result = fetch_current_weather("lagos", lat=6.5244, lon=3.3792)
print(result)
# Should print temp, humidity, wind etc.
"""

"""
# Fetch live AQI (after you have real location IDs)
from data_ingestion.openaq_fetcher import fetch_city_readings

df = fetch_city_readings("ibadan", location_ids=[6295420, 6299186, 6299190, 6299189, 6299185, 6299188, 6299187, 6299191])
print(df.head())
print(df["parameter"].unique())
"""

"""
from apps.api.app.db.database import check_db_connection
check_db_connection()
# Expected: ✅ Database connection healthy

"""