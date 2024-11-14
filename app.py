#importing the required library
import streamlit as st
import pandas as pd
import datetime as dt

st.title('RFM Analysis Model')

# File uploader widget
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

def calculate_rfm(df, customer_id_col, transaction_date_col, transaction_value_col):
    # Ensure the transaction date column is in datetime format
    df[transaction_date_col] = pd.to_datetime(df[transaction_date_col])
    
    # Define the current date (for recency calculation)
    now = dt.datetime.now()

    # Calculate RFM metrics
    rfm_df = df.groupby(customer_id_col).agg({
        transaction_date_col: lambda x: (now - x.max()).days,  # Recency
        transaction_value_col: 'sum',  # Monetary
        customer_id_col: 'count'  # Frequency
    }).rename(columns={
        transaction_date_col: 'Recency',
        transaction_value_col: 'Monetary',
        customer_id_col: 'Frequency'
    })
    
    # Function to apply qcut with dynamic binning
    def apply_qcut(column, num_bins):
        unique_values = column.nunique()
        if unique_values <= num_bins:
            return pd.cut(column, bins=num_bins, labels=False) + 1
        else:
            return pd.qcut(column, num_bins, labels=False, duplicates='drop') + 1
    num_bins = 4

    # Apply quantile binning
    rfm_df['R_Score'] = apply_qcut(rfm_df['Recency'], num_bins)
    rfm_df['F_Score'] = apply_qcut(rfm_df['Frequency'], num_bins)
    rfm_df['M_Score'] = apply_qcut(rfm_df['Monetary'], num_bins)



    # Combine R, F, M scores into one RFM score
    rfm_df['RFM_Score'] = rfm_df['R_Score'].astype(str) + rfm_df['F_Score'].astype(str) + rfm_df['M_Score'].astype(str)
    
    # Define customer segments
    def segment_customer(row):
        if row['R_Score'] >= 3 and row['F_Score'] >= 3 and row['M_Score'] >= 3:
            return 'Active'
        elif row['R_Score'] <= 2 and row['F_Score'] <= 2 and row['M_Score'] <= 2:
            return 'Inactive'
        elif row['R_Score'] <= 2 and row['F_Score'] >= 3 and row['M_Score'] >= 3:
            return 'Departing'
        elif row['R_Score'] >= 3 and row['F_Score'] <= 2 and row['M_Score'] <= 2:
            return 'New'
        else:
            return 'Other'
    
    # Apply segmentation function
    rfm_df['Segment'] = rfm_df.apply(segment_customer, axis=1)
    
    # Debugging: Check if Segment column is created
    #st.write("Columns in rfm_df after segmentation:", rfm_df.columns.tolist())
    
    return rfm_df

if uploaded_file is not None:
    # Load the CSV file into a DataFrame
    df = pd.read_csv(uploaded_file, encoding='unicode_escape')

    # Display the dataset preview
    st.write('Dataset Preview:')
    st.write(df)

    # Get the columns from the DataFrame
    columns = df.columns.tolist()

    # Allow user to select columns for Customer ID, Transaction Date, and Transaction Value
    customer_id_col = st.selectbox("Select the column for Customer ID:", columns)
    transaction_date_col = st.selectbox("Select the column for Transaction Date:", columns)
    transaction_value_col = st.selectbox("Select the column for Transaction Value:", columns)

    # Show the selected columns
    st.write(f"Customer ID column: {customer_id_col}")
    st.write(f"Transaction Date column: {transaction_date_col}")
    st.write(f"Transaction Value column: {transaction_value_col}")

    # Use the selected columns for further processing
    if st.button("Process Data"):
        # Calculate RFM metrics and segmentation
        rfm_df = calculate_rfm(df, customer_id_col, transaction_date_col, transaction_value_col)
        st.write("RFM Metrics and Segmentation:")
        st.write(rfm_df)

        # Print groups by segment
        st.write("Segmented Customer Groups:")
        for segment in ['Active', 'Inactive', 'Departing', 'New']:
            st.write(f"--- {segment} Customers ---")
            if 'Segment' in rfm_df.columns:
                #DataFrame to include only rows where the Segment column matches the current segment in the loop.
                segment_df = rfm_df[rfm_df['Segment'] == segment]
                st.write(segment_df)
            else:
                st.write(f"Segment column not found. Available columns: {rfm_df.columns.tolist()}")

# New Section: Single Customer RFM Analysis
st.subheader('Single Customer RFM analysis')
customer_id = st.text_input('enter customer ID:')
transaction_dates = st.text_area("Enter Transaction Dates (comma-separated in YYYY-MM-DD format):")
transaction_values = st.text_area("Enter Transaction Values (comma-separated):")

if st.button("Analyze single customer"):
    if customer_id and transaction_dates and transaction_values:
        transaction_dates_list = [dt.datetime.strptime(date.strip(), '%Y-%m-%d') for date in transaction_dates.split(',')]
        transaction_values_list = [float(value.strip())for value in transaction_values.split(',')]

    #create dataframe for single customer
    customer_df = pd.DataFrame({
            'CustomerID': [customer_id] * len(transaction_dates_list),
            'TransactionDate': transaction_dates_list,
            'TransactionValue': transaction_values_list
        })
    
    #calculate RFm metrics and segmentation for single customer
    single_customer_rfm_df = calculate_rfm(customer_df, 'CustomerID', 'TransactionDate', 'TransactionValue')


    # Display the RFM metrics and segment
    st.write("Single Customer RFM Metrics and Segmentation:")
    st.write(single_customer_rfm_df)
