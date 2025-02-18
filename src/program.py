from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut
import json

USER_AGENT = "ms10791@nyu.edu"
INPUT_MODE = False # if True, asks for inputs at runtime. if False, uses predefined inputs (for debugging)
BBOX_RADIUS_MILES = 5 # default radius for bounding box ("bbox") in miles
DEST_RADIUS_MILES = .5 # default radius for each dest1, to look for nearby dest2 + dest3

geolocator = Nominatim(user_agent=USER_AGENT, scheme="https", domain="nominatim.openstreetmap.org") # explicitly use the public api (vs. postgresql or local nominatim instance)

### location functions
def get_location_input():
    """get location input from the user."""
    location_input = input("""Input a location (the specificity is up to you, but supplying more details is better, e.g., "new york, new york, USA" vs "newyork"):  """)
    return location_input

def save_location_to_file(location, bbox, add_bbox, radius_miles):
    """save the JSON response to a file."""
    location_data = location.raw
    location_data["bbox"] = bbox
    location_data["add_bbox"] = add_bbox
    location_data["radius_miles"] = radius_miles
    with open("location.json", "w") as json_file:
        json.dump(location_data, json_file, indent=4)

def read_location_from_file():
    """read the JSON response from a file."""
    with open("location.json", "r") as json_file:
        location_data = json.load(json_file)
    return location_data

def create_bbox(lat, lon, radius_miles):
    """create a bounding box with a given radius around a location."""
    origin = (lat, lon)
    top = geodesic(miles=radius_miles).destination(origin, 0).latitude
    bottom = geodesic(miles=radius_miles).destination(origin, 180).latitude
    right = geodesic(miles=radius_miles).destination(origin, 90).longitude
    left = geodesic(miles=radius_miles).destination(origin, 270).longitude
    return [bottom, top, left, right] # following *Nominatim* format (https://wiki.openstreetmap.org/wiki/Bounding_box)

def is_within_bbox(lat, lon, bbox):
    """check if a point is within a bounding box."""
    bottom, top, left, right = bbox
    return bottom <= lat <= top and left <= lon <= right

def calculate_radius_to_encompass_bbox(lat, lon, bbox):
    """calculate the radius in miles to encompass the entire bounding box."""
    bottom, top, left, right = map(float, bbox)
    center = (lat, lon)
    point1 = (bottom, left)  # bottom-left corner
    point2 = (top, right)    # top-right corner
    distances = [
        geodesic(center, point1).miles,
        geodesic(center, point2).miles,
    ]
    return max(distances)

def process_bbox_and_create_new_bbox(location_data):
    """process the bounding box, calculate the midpoint, and create a new bounding box around the midpoint."""
    bbox = location_data.get("bbox", [])
    if bbox:
        lat = location_data.get("lat")
        lon = location_data.get("lon")

        radius_miles = calculate_radius_to_encompass_bbox(lat, lon, bbox)
        new_bbox = create_bbox(lat, lon, radius_miles)
        # print(f"""
        # New Bounding Box:
        # Bottom: {new_bbox[0]}
        # Top: {new_bbox[1]}
        # Left: {new_bbox[2]}
        # Right: {new_bbox[3]}
        
        # Radius to Encompass Bounding Box: {radius_miles} miles
        # """)
        return new_bbox, radius_miles
    else:
        print("\nBounding box not found in the JSON response.\n")
        return None, None

def process_location(location, radius_miles):
    """process location and save to file."""
    print(f"""
    Location Address: {location.address}
    Latitude: {location.latitude}
    Longitude: {location.longitude}
    """)
    bbox = location.raw.get("boundingbox", [])
    if not bbox:
        bbox = create_bbox(location.latitude, location.longitude, radius_miles)
        add_bbox = True
    else:
        add_bbox = False
    radius_miles = calculate_radius_to_encompass_bbox(location.latitude, location.longitude, bbox)
    save_location_to_file(location, bbox, add_bbox, radius_miles)

def handle_location_input(radius_miles):
    """handle location input and save to file."""
    unconfirmed_input = True
    while unconfirmed_input: # loop until 1) successful location search and 2) user confirmation
        location_input = get_location_input()
        location = retry_geocode(location_input, geolocator)
        if location:
            print(f"""
            Location Address: {location.address}
            Latitude: {location.latitude}
            Longitude: {location.longitude}
            """)
            # print(location.raw) # for debugging: print the entire json response

            confirmation = input("Is this the correct location? (y/n):  ")
            if confirmation.lower().strip() == "y":
                print("\nLocation confirmed. Continuing...\n")
                process_location(location, radius_miles)
                break

        else:
            print("\nLocation not found.\n")
        print("Retrying... redo your location input...\n")

def handle_hardcoded_location(radius_miles):
    """handle hardcoded location and save to file."""
    hardcoded_location = "new york, new york, USA"
    location = retry_geocode(hardcoded_location, geolocator)
    process_location(location, radius_miles)

def clear_location_file():
    """clear the location.json file."""
    with open("location.json", "w") as json_file:
        json_file.write("{}")

def get_user_destinations():
    """prompt the user for three destinations, ranked by importance."""

    if not INPUT_MODE:
        return ["park", "book shop", "bakery"]
    
    print("Please enter 3 destinations you are interested in, ranked by importance.\nDestination list: https://wiki.openstreetmap.org/wiki/Nominatim/Special_Phrases/EN")
   
    destinations = []
    for i in range(1, 4):
        destination = input(f"Enter destination {i}: ").strip().lower()
        destinations.append(destination)
    return destinations

def retry_geocode(query, geolocator=None, *args, **kwargs):
    """Retry geocode call until successful."""
    if geolocator is None:
        geolocator = Nominatim(user_agent=USER_AGENT, scheme="https", domain="nominatim.openstreetmap.org")
    try:
        return geolocator.geocode(query, *args, **kwargs)
    except GeocoderTimedOut:
        print("GeocoderTimedOut: Retrying...")
        return retry_geocode(query, geolocator, *args, **kwargs)

def query_destinations(location_data, bbox, destination_type, limit=50):
    """query geocode for each destination type within the bounding box."""
    bottom, top, left, right = bbox
    query = f"{destination_type} near {location_data['display_name']}"
    
    try:
        # correct format for viewbox
        viewbox = [(bottom, left), (top, right)]
        results = retry_geocode(
            query, 
            geolocator,
            exactly_one=False, 
            viewbox=viewbox, 
            bounded=True, 
            timeout=None,
            limit=limit # max number of results to return. Nominatim caps it at 50
        )
        print(results)
    except Exception as e:
        print(f"Error: {e}")
        raise
    
    return results

def save_destinations_to_file(destinations, filename):
    """save the destination results to a json file."""
    serializable_destinations = []
    for destination in destinations:
        serializable_destinations.append({
            "address": destination.address,
            "latitude": destination.latitude,
            "longitude": destination.longitude,
            "raw": destination.raw
        })
    with open(filename, "w") as json_file:
        json.dump(serializable_destinations, json_file, indent=4)


def count_items_in_json(filename):
    with open(filename, 'r') as json_file:
        data = json.load(json_file)
        return len(data)

def process_destinations(dest1_file, dest2_file, dest3_file, hits_file, radius_miles=1):
    """process destinations and find hits within bounding boxes."""
    with open(dest1_file, 'r') as file:
        dest1_data = json.load(file)
    
    with open(dest2_file, 'r') as file:
        dest2_data = json.load(file)
    
    with open(dest3_file, 'r') as file:
        dest3_data = json.load(file)
    
    hits = []

    for dest1 in dest1_data:
        lat1 = dest1['latitude']
        lon1 = dest1['longitude']
        bbox1 = create_bbox(lat1, lon1, radius_miles)
        
        hits2 = [dest2 for dest2 in dest2_data if is_within_bbox(dest2['latitude'], dest2['longitude'], bbox1)]
        hits3 = [dest3 for dest3 in dest3_data if is_within_bbox(dest3['latitude'], dest3['longitude'], bbox1)]
        
        if hits2 or hits3:
            hits.append({
                'hits1': dest1,
                'hits2': hits2,
                'hits3': hits3
            })
    
    with open(hits_file, 'w') as file:
        json.dump(hits, file, indent=4)

def print_json_file_sizes(filenames):
    """Print the number of items in each JSON file."""
    for filename in filenames:
        num_items = count_items_in_json(filename)
        print(f'The number of items in {filename} is {num_items}.')

def count_hits(hits_file):
    """Count the number of items in hits2 and hits3 for each hits1."""
    with open(hits_file, 'r') as file:
        hits_data = json.load(file)
    
    hits_count = {}
    
    for entry in hits_data:
        hits1 = entry['hits1']
        name = hits1['raw'].get('name') or hits1['address'].split(',')[0]
        hits2_count = len(entry['hits2'])
        hits3_count = len(entry['hits3'])
        
        hits_count[name] = {
            'hits2': hits2_count,
            'hits3': hits3_count
        }
    
    return hits_count

### main function
def main(radius_miles=BBOX_RADIUS_MILES):

    # get location; save to file
    if INPUT_MODE: # ask for location inputs at runtime
        handle_location_input(radius_miles)
    else: # 'debugging mode' - use a hardcoded location
        handle_hardcoded_location(radius_miles)

    # get the bounding box for the search area (create if it doesn't exist)
    location_data = read_location_from_file()
    new_bbox, radius_miles = process_bbox_and_create_new_bbox(location_data)

    # get user destinations
    destinations = get_user_destinations()

    # query geocode for each destination type and save results to json files
    for i, destination in enumerate(destinations):
        results = query_destinations(location_data, new_bbox, destination)
        save_destinations_to_file(results, f"dest{i+1}.json")

    # process destinations and find hits within bounding boxes
    process_destinations(
        dest1_file='/Users/marissashey/Documents/GitHub/mappy/dest1.json',
        dest2_file='/Users/marissashey/Documents/GitHub/mappy/dest2.json',
        dest3_file='/Users/marissashey/Documents/GitHub/mappy/dest3.json',
        hits_file='/Users/marissashey/Documents/GitHub/mappy/hits.json'
    )

    # print the number of items in each JSON file
    json_files = [
        '/Users/marissashey/Documents/GitHub/mappy/dest1.json',
        '/Users/marissashey/Documents/GitHub/mappy/dest2.json',
        '/Users/marissashey/Documents/GitHub/mappy/dest3.json',
        '/Users/marissashey/Documents/GitHub/mappy/hits.json'
    ]
    print_json_file_sizes(json_files)

    # count hits in hits.json
    hits_count = count_hits('/Users/marissashey/Documents/GitHub/mappy/hits.json')
    print(hits_count)

    # clear location.json at the end of the program run
    # clear_location_file()

if __name__ == "__main__":
    main()