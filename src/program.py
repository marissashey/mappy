from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import json

USER_AGENT = "ms10791@nyu.edu"
INPUT_MODE = False # if True, asks for inputs at runtime. if False, uses predefined inputs (for debugging)

geolocator = Nominatim(user_agent=USER_AGENT, scheme="https", domain="nominatim.openstreetmap.org") # explicitly use the public api (vs. postgresql or local nominatim instance)

def get_location_input():
    """get location input from the user."""
    location_input = input("""Input a location (the specificity is up to you, but supplying more details is better, e.g., "new york, new york, USA" vs "newyork"):  """)
    return location_input

def save_location_to_file(location, bounding_box, add_bounding_box):
    """save the JSON response to a file."""
    location_data = location.raw
    location_data["boundingbox"] = bounding_box
    location_data["add_bounding_box"] = add_bounding_box
    with open("location.json", "w") as json_file:
        json.dump(location_data, json_file, indent=4)

def read_location_from_file():
    """read the JSON response from a file."""
    with open("location.json", "r") as json_file:
        location_data = json.load(json_file)
    return location_data

def extract_and_print_bounding_box(location_data):
    """extract and print the bounding box coordinates."""
    bounding_box = location_data.get("boundingbox", [])
    if bounding_box:
        south, north, west, east = map(float, bounding_box)
        print(f"Bounding Box: South: {south}, North: {north}, West: {west}, East: {east}")
    else:
        print("Bounding box not found in the JSON response.")

def create_bounding_box(lat, lon, radius_miles=5):
    """create a bounding box with a given radius around a location."""
    origin = (lat, lon)
    north = geodesic(miles=radius_miles).destination(origin, 0).latitude
    south = geodesic(miles=radius_miles).destination(origin, 180).latitude
    east = geodesic(miles=radius_miles).destination(origin, 90).longitude
    west = geodesic(miles=radius_miles).destination(origin, 270).longitude
    return [south, north, west, east]

def handle_location_input():
    """handle location input and save to file."""
    unconfirmed_input = True
    while unconfirmed_input: # loop until 1) successful location search and 2) user confirmation
        location_input = get_location_input()
        location = geolocator.geocode(location_input)
        if location:
            print(location.address)
            print(location.latitude, location.longitude)
            # print(location.raw) # for debugging: print the entire json response

            confirmation = input("Is this the correct location? (y/n):  ")
            if confirmation.lower().strip() == "y":
                print("Location confirmed. Continuing...")
                bounding_box = location.raw.get("boundingbox", [])
                if not bounding_box:
                    bounding_box = create_bounding_box(location.latitude, location.longitude)
                    add_bounding_box = True
                else:
                    add_bounding_box = False
                save_location_to_file(location, bounding_box, add_bounding_box)
                break

        else:
            print("Location not found.")
        print("Retrying... redo your location input...")

def handle_hardcoded_location():
    """handle hardcoded location and save to file."""
    hardcoded_location = "cupertino, california"
    location = geolocator.geocode(hardcoded_location)
    print(hardcoded_location)
    print(location.address)
    print(location.latitude, location.longitude)
    bounding_box = location.raw.get("boundingbox", [])
    if not bounding_box:
        bounding_box = create_bounding_box(location.latitude, location.longitude)
        add_bounding_box = True
    else:
        add_bounding_box = False
    save_location_to_file(location, bounding_box, add_bounding_box)

def clear_location_file():
    """clear the location.json file."""
    with open("location.json", "w") as json_file:
        json_file.write("{}")

def main():
    if INPUT_MODE: # ask for location inputs at runtime
        handle_location_input()
    else: # 'debugging mode' - use a hardcoded location
        handle_hardcoded_location()

    # geocode request is now saved in location.json -> get coordinates + bounding box
    location_data = read_location_from_file()
    extract_and_print_bounding_box(location_data)

    # clear location.json at the end of the program run
    clear_location_file()

if __name__ == "__main__":
    main()