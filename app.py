from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Verify that the environment variables are loaded correctly
print(os.getenv("SNOWFLAKE_ACCOUNT"))  # This should print your Snowflake account

# Define connection parameters using the loaded environment variables
CONNECTION_PARAMETERS = {
    'account': os.getenv("SNOWFLAKE_ACCOUNT"),
    'user': os.getenv("SNOWFLAKE_USER"),
    'password': os.getenv("SNOWFLAKE_PASSWORD"),
    'role': os.getenv("SNOWFLAKE_ROLE"),
    'warehouse': os.getenv("SNOWFLAKE_WAREHOUSE"),
    'database': os.getenv("SNOWFLAKE_DATABASE"),
    'schema': os.getenv("SNOWFLAKE_SCHEMA")
}

# Print the connection parameters to verify
print(CONNECTION_PARAMETERS)
