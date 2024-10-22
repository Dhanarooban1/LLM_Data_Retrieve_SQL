from dotenv import load_dotenv
load_dotenv()  # Load environment variables

import streamlit as st
import os
import sqlite3
import google.generativeai as genai

# Configure GenAI Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the model globally once
model = genai.GenerativeModel('gemini-pro')

# Function to load Google Gemini Model and provide queries as response
def get_gemini_response(question, prompt):
    try:
        response = model.generate_content([prompt[0], question])
        return response.text.strip()  # Strip whitespace for clean SQL response
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return None

# Function to retrieve query from the database
def read_sql_query(sql, db):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        # Capture the SQL error and return it to regenerate the query
        st.error(f"SQL Error: {e}")
        return str(e)
    finally:
        conn.close()  # Ensure connection is closed after querying

# Function to regenerate SQL query based on an error message
def regenerate_sql_query(question, error_message, prompt):
    new_prompt = prompt[0] + f"\nNote: The following error occurred with the previous query: {error_message}.\nPlease correct the query."
    return get_gemini_response(question, [new_prompt])

# Define the prompt
prompt = [
    """
    You are an expert in converting English questions to SQL query!
    The SQL database has the name STUDENT and has the following columns - NAME, CLASS, 
    SECTION. \n\nFor example,\nExample 1 - How many entries of records are present?, 
    the SQL command will be something like this SELECT COUNT(*) FROM STUDENT ;
    \nExample 2 - Tell me all the students studying in Data Science class?, 
    the SQL command will be something like this SELECT * FROM STUDENT 
    where CLASS="Data Science"; 
    also the sql code should not have ``` in beginning or end and sql word in output
    """
]

# Streamlit App
st.set_page_config(page_title="I can Retrieve Any SQL query")
st.header("Gemini App To Retrieve SQL Data")

question = st.text_input("Input your question:", key="input")

submit = st.button("Ask the question")

# If submit button is clicked
if submit:
    with st.spinner("Fetching response..."):
        sql_query = get_gemini_response(question, prompt)
        
        if sql_query:
            st.write(f"Generated SQL Query: `{sql_query}`")  # Show the initial SQL query

            # Fetch data from the database
            response = read_sql_query(sql_query, "student.db")

            # Check if we got an error message instead of data rows
            while isinstance(response, str):  # If response is an error message, it's a string
                st.warning("The query failed due to an error. Attempting to fix...")
                
                # Regenerate SQL query based on the error message
                sql_query = regenerate_sql_query(question, response, prompt)
                st.write(f"Attempting with the new query: `{sql_query}`")
                
                # Re-run the SQL query
                response = read_sql_query(sql_query, "student.db")

            if response:
                st.subheader("Query Results:")
                for row in response:
                    st.write(row)
            else:
                st.warning("No data found for the given query.")
        else:
            st.error("Failed to generate a valid SQL query. Please try again.")
