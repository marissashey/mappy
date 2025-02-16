# installation steps

1. create + activate your virtual environment:

    ```sh
    python -m venv .venv
    source .venv/bin/activate
    ```

2. install requirement files:

    ```sh
    pip install -r requirements.txt
    ```

3. in `program.py`, overwrite `USER_AGENT` 
    i.e., make a unique string to get past Nominatim 's spam filter.
    this is effectively your open source API key; for large numbers of requests include your email address.

    ```python
    USER_AGENT = your_unique_id_here
    geolocator = Nominatim(user_agent=USER_AGENT, ... )
    ```
