from geopy.geocoders import Nominatim
USER_AGENT = "ms10791@nyu.edu"
INPUT_MODE = True # if True, asks for inputs at runtime.  if False, uses predefined inputs (for debugging)
 
geolocator = Nominatim(user_agent=USER_AGENT, scheme="https", domain="nominatim.openstreetmap.org") # explicily use the public api (vs. postgresql or local nominatim instance)

if INPUT_MODE:
    unconfirmed_input = True
    while unconfirmed_input:
        location_input = input("Input location [format: city, state]:  ")
        location = geolocator.geocode(location_input)
        if location:
            print(location.address)
            print(location.latitude, location.longitude)
            # print(location.raw)

            confirmation = input("Is this the correct location? (y/n):  ")
            if confirmation.lower().strip() == "y":
                print("Location confirmed. Continuing...")
                break
            
        else:
            print("Location not found.")
        print("Retrying... redo your location input...")
    
else: 
    hardcoded_location = "cupertino, california"
    location = geolocator.geocode(hardcoded_location)
    print(location.address)
    print(location.latitude, location.longitude)

