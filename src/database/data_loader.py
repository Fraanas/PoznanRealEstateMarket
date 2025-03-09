from .db_connector import create_connection
import logging

logger = logging.getLogger(__name__)

def insert_data(data):
    """
    :param data:
    :return:
    """
    try:
        connection = create_connection()
        cursor = connection.cursor()

        # Query to insert data
        insert_query = insert_query = """
            INSERT INTO properties (property_id, price, square, price_per_sqm, rooms,
            date, url, street, district_1, district_2, city, state) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (property_id) DO NOTHING;
        """

        # Insert multiple rows of data
        cursor.executemany(insert_query, data)
        connection.commit()

        cursor.close()
        connection.close()
        logger.info(f"Successfully inserted {len(data)} rows into database.")

    except Exception as e:
        logger.error(f"Error inserting data into the database: {e}")
        if connection:
            connection.rollback()
        raise
