# set up 

1. **create + activate your virtual environment**:

    ```sh
    python -m venv .venv
    source .venv/bin/activate
    ```

2. **install requirement files**:

    ```sh
    pip install -r requirements.txt
    ```

3. **in `program.py`, overwrite `USER_AGENT`**:

    this is effectively your open-source API key; for large numbers of requests include your email address.

    ```python
    USER_AGENT = your_unique_id_here
    geolocator = Nominatim(user_agent=USER_AGENT, ... )
    ```

4. **run the program**:

```sh
python src/program.py
```


## resources

- geopy documentation: https://geopy.readthedocs.io/en/stable/index.html?highlight=user_agent
- nominatim special phrases: https://wiki.openstreetmap.org/wiki/Nominatim/Special_Phrases/EN
