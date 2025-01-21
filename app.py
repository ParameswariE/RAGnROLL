# Import necessary packages
import streamlit as st
import json
import re
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, parse_json
from trulens.core import TruSession
from trulens.connectors.snowflake import SnowflakeConnector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

CONNECTION_PARAMETERS = {
    'account': os.getenv("SNOWFLAKE_ACCOUNT"),
    'user': os.getenv("SNOWFLAKE_USER"),
    'password': os.getenv("SNOWFLAKE_PASSWORD"),
    'role': os.getenv("SNOWFLAKE_ROLE"),
    'warehouse': os.getenv("SNOWFLAKE_WAREHOUSE"),
    'database': os.getenv("SNOWFLAKE_DATABASE"),
    'schema': os.getenv("SNOWFLAKE_SCHEMA")
}

# Create a Snowflake session
snowpark_session = Session.builder.configs(CONNECTION_PARAMETERS).create()

# Function to extract location and store name from user query
def extract_location_and_store(query):
    # Simple regex to extract location and store name (can be improved with NLP)
    location_match = re.search(r'in\s+(\w+)', query, re.IGNORECASE)
    store_match = re.search(r'open\s+(\w+)', query, re.IGNORECASE)
    location = location_match.group(1) if location_match else None
    store_name = store_match.group(1) if store_match else None
    return location, store_name

# Streamlit app header
st.title("AI-Powered News Search and Summary with TruLens and Snowflake")
st.write("Search for articles, retrieve relevant results, and generate insightful summaries in your preferred language!")

# Initialize Snowflake and TruLens sessions
conn = SnowflakeConnector(snowpark_session=snowpark_session)
tru_session = TruSession(connector=conn)

# Chatbot input from the user
st.header("Retail Location Analysis Chatbot")
user_query = st.text_input("Ask a question about retail opportunities (e.g., 'Can I open Walmart in London?'):")

if user_query:
    st.write(f"Analyzing query: {user_query}")

    try:
        # Extract location and store name from user query
        location, store_name = extract_location_and_store(user_query)
        if not location or not store_name:
            st.write("Could not extract location or store name from the query. Please try again.")
        else:
            # Cortex Search query construction
            search_service_name = "MY_SAFEGRAPH.PUBLIC.S"  # Update with your actual Cortex Search Service name
            query = f"""
                SELECT PARSE_JSON(
                    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                        '{search_service_name}',
                        '{{"query": "{location}", "columns": ["LOCATION_NAME", "CATEGORY_TAGS", "STREET_ADDRESS", "CITY", "POSTAL_CODE", "LATITUDE", "LONGITUDE", "WKT_AREA_SQ_METERS", "OPEN_HOURS", "CLOSED_ON"], "limit": 5}}'
                    )
                )['results'] AS results
            """

            # Execute the query to get search results from Cortex Search
            search_results = snowpark_session.sql(query).collect()

            if not search_results:
                st.write("No relevant data found. Try a different query.")
            else:
                # Parse the JSON results
                results_list = json.loads(search_results[0]["RESULTS"])
                if not results_list:
                    st.write("No relevant data found. Try a different query.")
                else:
                    # Select the first result for simplicity
                    selected_location = results_list[0]

                    # Generate insights using Mistral LLM via Cortex AI
                    st.subheader("Location Recommendation")
                    try:
                        # Properly format the JSON data for the query
                        location_data = json.dumps(selected_location).replace("'", "''")
                        insights_query = f"""
                            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                                'mistral-large2',
                                'Based on the provided data, is it a good idea to open a {store_name} in {location}? {location_data}'
                            ) AS INSIGHTS
                        """
                        insights_result = snowpark_session.sql(insights_query).collect()
                        insights = insights_result[0]["INSIGHTS"]
                        st.write(insights)
                    except Exception as e:
                        st.error(f"Error generating insights: {e}")
    except Exception as e:
        st.error(f"Error retrieving data: {e}")

# Close the session when the app stops
snowpark_session.close()
