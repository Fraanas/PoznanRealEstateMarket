import logging
from datetime import datetime

def transform_float(value):
    """Converts a value to float if it's not None, otherwise returns None."""
    return float(value) if value is not None else None


def transform_int(value):
    """Converts a value to int if it's not None, otherwise returns None."""
    return int(value) if value is not None else None

def transform_date(value):
    """Converts a value to date (YYYY-MM-DD) if it's not None, otherwise returns None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date('%Y-%m-%d')

    possible_formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']
    for f in possible_formats:
        try:
            return datetime.strptime(value, f).strftime('%Y-%m-%d')
        except ValueError:
            continue

    return None

def transform_price(price):
    """Converts price to float or None if price is unavailable."""
    if price == 'Zapytajocenę' or price is None:
        return None
    if isinstance(price, float):  # If it is already a float, we return unchanged
        return price
    return float(price.replace(',', '.')) if isinstance(price, str) else None





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
    city = location_elements[3].strip() if location_elements[3] else 'Poznań'
    state = location_elements[4].strip() if location_elements[4] else 'wielkopolskie'

    for district in [district_1, district_2]:
        if district and 'Poznań' in district:
            city = 'Poznań'
            district = None
        if district and 'wielkopolskie' in district:
            state = 'wielkopolskie'
            district = None

    return street, district_1, district_2, city, state


def transform_info(info):
    """
    Parses scraped HTML data into a structured dictionary.
    Args:
        info (list or str): List of BeautifulSoup elements or a string containing property information.
    Returns:
        dict: Dictionary with extracted key-value pairs.
    """
    if not info:
        return {}

    data = {}

    for i in range(0, len(info) - 1, 2):
        key = info[i].text.strip().replace("<!-- -->:", "").strip()
        value = info[i + 1].text.strip()

        if value.lower() == 'brak informacji':
            value = None

        data[key] = value

    return data


def unpack_dict(dict, *keys, **default_values):
    """
    Function that unpacks selected keys from a dictionary.

    Parameters:
    - dictionary: dictionary to unpack
    - *keys: keys we want to extract
    - **default_values: default values for missing keys

    Returns:
    - tuple containing values for the provided keys
    """
    results = []

    for key in keys:
        if key in dict:
            results.append(dict[key])
        elif key in default_values:
            results.append(default_values[key])
        else:
            results.append(None)

    if len(results) == 1:
        return results[0]
    return tuple(results)


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

    data['price'] = transform_price(data.get('price'))
    data['square'] = transform_float(data.get('square'))
    data['rooms'] = transform_int(data.get('rooms'))
    #data['price_per_sqm'] = transform_float(data.get('price_per_sqm'))

    # Transform location and assign values
    data['street'], data['district_1'], data['district_2'], data['city'], data['state'] = transform_location(
        data.get('location'))

    column_mapping = {
        "Ogrzewanie": "heating",
        "Piętro": "floor",
        "Czynsz": "rent",
        "Stan wykończenia": "bld_condition",
        "Rynek": "market",
        "Forma własności": "ownership",
        "Dostępne od": "availability",
        "Typ ogłoszeniodawcy": "seller_type",
        "Informacje dodatkowe": "extra_info",
        "Winda": "elevator",
        "Rodzaj zabudowy": "building_type",
        "Rok budowy": "building_year",
        "Zabezpieczenia": "security",
        "Media": "media",
        "Materiał budynku": "building_material",
        "Okna": "windows",
        "Wyposażenie": "equipment"
    }

    # Get info and map column names
    info_data = data.get('info', {})
    mapped_info = {column_mapping[k]: v for k, v in info_data.items() if k in column_mapping} if isinstance(info_data,
                                                                                                            dict) else {}

    # Update data with mapped info
    data.update(mapped_info)

    # Core fields to keep
    allowed_fields = [
                         "property_id", "price", "square", "price_per_sqm", "rooms", "date", "url",
                         "street", "district_1", "district_2", "city", "state"
                     ] + list(column_mapping.values())

    # Keep only allowed columns
    filtered_data = {k: v for k, v in data.items() if k in allowed_fields}

    # Convert specific fields
    if 'availability' in filtered_data:
        filtered_data['availability'] = transform_date(filtered_data['availability'])

    return filtered_data


