import numpy as np

'''
def transform_to_none(data):
    """
    Converts empty values in the dictionary to None.
    Args:       data (dict): Data to be converted
    Returns:    dict: Data with empty values replaced with None
    """
    if not data:
        return {}

    empty_values = {None, "", " ", "NaN", "NULL", "<null>", np.nan}  # Handling different formats of empty values

    def is_empty(value):
        """Checks whether the value should be converted to None."""
        if value in empty_values or (isinstance(value, str) and value.strip() in empty_values):
            return True
        return False

    return {key: None if is_empty(value) else value for key, value in data.items()}
'''

def transform_to_none(data):
    """Recursively converts empty strings and '<null>' values to None in a dictionary or list."""
    for key, value in data.items():
        if isinstance(value, list):
            data[key] = [None if item == '' else item for item in value]
        else:
            data[key] = None if value == '' else value

    return data



def transform_float(value):
    """Converts a value to float if it's not None, otherwise returns None."""
    return float(value) if value is not None else None


def transform_int(value):
    """Converts a value to int if it's not None, otherwise returns None."""
    return int(value) if value is not None else None


def transform_price(price):
    """Converts price to float or None if price is unavailable."""
    if price == 'Zapytajocenę':
        return None
    return float(price.replace(',', '.')) if price else None

'''
def transform_location(location):
    """Splits location into separate components: street, district_1, district_2, city, state."""
    if not location:
        return None, None, None, None, None

    location_elements = location.split(',')

    # Ensure we have exactly 5 elements (fill missing with None)
    while len(location_elements) < 5:
        location_elements.append(None)

    street = location_elements[0].replace('ul.', '').strip() if location_elements[0] and 'ul.' in location_elements[0] else None
    district_1 = location_elements[1].strip() if location_elements[1] else None
    district_2 = location_elements[2].strip() if location_elements[2] else None
    city = location_elements[3].strip() if location_elements[3] else None
    state = location_elements[4].strip() if location_elements[4] else None

    return street, district_1, district_2, city, state
'''
def transform_location(location):
    """Splits location into separate components: street, district_1, district_2, city, state."""
    if not location:
        return None, None, None, None, None

    location_elements = location.split(',')

    # Ensure we have exactly 5 elements (fill missing with None)
    while len(location_elements) < 5:
        location_elements.append(None)

    street = location_elements[0].replace('ul.', '').strip() if location_elements[0] and 'ul.' in location_elements[0] else None
    district_1 = location_elements[1].strip() if location_elements[1] else None
    district_2 = location_elements[2].strip() if location_elements[2] else district_1

    # Przypisanie "Poznań" i "Wielkopolskie" do city i state, jeśli ich brakuje
    city = location_elements[3].strip() if location_elements[3] else 'Poznań'
    state = location_elements[4].strip() if location_elements[4] else 'wielkopolskie'

    for district in [district_1, district_2]:
        if district and 'Poznań' in district:
            city = 'Poznań'
            district = None  # Wyczyść district, jeśli zawiera "Poznań"
        if district and 'wielkopolskie' in district:
            state = 'wielkopolskie'
            district = None  # Wyczyść district, jeśli zawiera "Wielkopolskie"

    return street, district_1, district_2, city, state

def transform_data(data):
    """
    Transforms the scraped data into the correct data types.

    Args:
        data (dict): Raw data of the property

    Returns:
        dict: Transformed data with correct types
    """
    if not data:
        return {}
    # Convert empty values to None
    data = transform_to_none(data)
    data['price'] = transform_price(data.get('price'))
    #data['square'] = transform_float(data.get('square'))
    #data['room'] = transform_int(data.get('room'))
    #data['price_per_sqm'] = transform_float(data.get('price_per_sqm'))

    # Transform location and assign values
    data['street'], data['district_1'], data['district_2'], data['city'], data['state'] = transform_location(
        data.get('location'))

    # Remove original location key
    data.pop('location', None)

    return data


