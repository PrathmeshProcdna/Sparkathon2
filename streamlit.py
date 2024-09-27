import streamlit as st
import pandas as pd  # Import pandas for DataFrame handling
from SM_insights import SM  # Replace with your actual Python file name

# Initialize your PostAnalyzer object
obj = SM()

# Streamlit app layout
st.title("PrepUp")

# Input field for NPI_ID
npi_id = st.text_input("Enter NPI_ID")

# Button to trigger response generation
if st.button("Analyze Post"):
    if npi_id:
        # Call the response method from the SM class
        ans = obj.response(npi_id)
        
        # Display the result
        if isinstance(ans, str):
            st.write(ans)  # Display the no results message
        else:
            # Assuming ans is a list of dictionaries (JSON-like format)
            df = pd.DataFrame(ans)  # Convert the results to a DataFrame
            
            st.write("Results:")
            st.dataframe(df)  # Display the DataFrame as a table
    else:
        st.write("Please enter a valid NPI_ID.")


