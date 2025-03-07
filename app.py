# Import necessary packages
import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col
from trulens.core import Tru
from trulens.connectors.snowflake import SnowflakeConnector
from dotenv import load_dotenv
import os
from snowflake.snowpark import Session
import atexit

load_dotenv()

CONNECTION_PARAMETERS = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
}

# Create a Snowflake session
snowpark_session = Session.builder.configs(CONNECTION_PARAMETERS).create()

# Register a cleanup function to close the session
atexit.register(lambda: snowpark_session.close())

# Streamlit app header
st.title("AI-Powered News Search and Summary")
st.write("Search for articles, retrieve relevant results, and generate insightful summaries in your preferred language!")

# Initialize Snowflake and TruLens sessions
conn = SnowflakeConnector(snowpark_session=snowpark_session)
tru = Tru()  # Initialize TruLens

# Language selection
st.header("Choose Language")
languages = {"English": "en", "French": "fr", "Spanish": "es", "German": "de", "Chinese": "zh"}
selected_language = st.selectbox("Select your preferred language:", options=list(languages.keys()))

# Search input from the user
st.header("Search Articles")
search_query = st.text_input("Enter a keyword or ask a question to find relevant articles:")

if search_query:
    st.write(f"Searching for articles related to: **{search_query}**")

    # Perform a search query using Snowflake SQL
    query = f"""
        SELECT ID, HEADLINE, CONTENT, RELATED_ARTICLES 
        FROM MY_NEWS_TABLE
        WHERE CONTAINS(CONTENT, '{search_query}') OR CONTAINS(HEADLINE, '{search_query}')
        LIMIT 5
    """
    try:
        search_results = snowpark_session.sql(query).collect()
        if not search_results:
            st.write("No relevant articles found. Try another search query.")
        else:
            # Display search results
            st.subheader("Search Results")
            article_dict = {row["ID"]: row["HEADLINE"] for row in search_results}
            selected_article_id = st.selectbox("Select an Article:", options=list(article_dict.keys()), format_func=lambda x: article_dict[x])

            # Check if an article is selected
            if selected_article_id:
                # Display selected article details
                selected_article = next(row for row in search_results if row["ID"] == selected_article_id)
                st.write(f"**Headline:** {selected_article['HEADLINE']}")
                st.write(f"**Content (Snippet):** {selected_article['CONTENT'][:500]}...")  # Show first 500 characters

                # Button to generate summary
                if st.button("Generate Summary"):
                    st.header("Generated Summary")
                    try:
                        # Escape content for safe SQL usage
                        escaped_content = selected_article["CONTENT"].replace("'", "''")

                        # Generate summary using Snowflake Cortex AI
                        summary_query = f"""
                            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                                'mistral-large2',
                                'Summarize this text: {escaped_content}'
                            ) AS SUMMARY
                        """
                        summary_result = snowpark_session.sql(summary_query).collect()
                        summary = summary_result[0]["SUMMARY"]

                        # Translate summary into selected language
                        translation_query = f"""
                            SELECT SNOWFLAKE.CORTEX.TRANSLATE(
                                '{summary.replace("'", "''")}',
                                'en',
                                '{languages[selected_language]}'
                            ) AS TRANSLATED_SUMMARY
                        """
                        translation_result = snowpark_session.sql(translation_query).collect()
                        translated_summary = translation_result[0]["TRANSLATED_SUMMARY"]

                        st.write(f"**Translated Summary ({selected_language}):**")
                        st.write(translated_summary)

                        # Like/Dislike buttons for feedback
                        st.write("Was this summary helpful?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("👍 Like"):
                                st.success("Thank you for your feedback!")
                        with col2:
                            if st.button("👎 Dislike"):
                                st.error("Thank you for your feedback!")
                    except Exception as e:
                        st.error(f"Error generating summary: {e}")
    except Exception as e:
        st.error(f"Error during search: {e}")
