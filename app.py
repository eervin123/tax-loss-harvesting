import streamlit as st
import pandas as pd

# Dictionary of state tax rates
state_tax_rates = {
    'AL': 5.0,   'AK': 0.0,   'AZ': 4.5,   'AR': 5.9,  'CA': 13.3, 'CO': 4.55,
    'CT': 6.99,  'DE': 6.6,   'FL': 0.0,   'GA': 5.75, 'HI': 11.0, 'ID': 6.925,
    'IL': 4.95,  'IN': 3.23,  'IA': 8.53,  'KS': 5.7,  'KY': 5.0,  'LA': 6.0,
    'ME': 7.15,  'MD': 5.75,  'MA': 5.0,   'MI': 4.25, 'MN': 9.85, 'MS': 5.0,
    'MO': 5.4,   'MT': 6.9,   'NE': 6.84,  'NV': 0.0,  'NH': 5.0,  'NJ': 10.75,
    'NM': 5.9,   'NY': 8.82,  'NC': 5.25,  'ND': 2.9,  'OH': 4.797, 'OK': 5.0,
    'OR': 9.9,   'PA': 3.07,  'RI': 5.99,  'SC': 7.0,  'SD': 0.0,  'TN': 0.0,
    'TX': 0.0,   'UT': 4.95,  'VT': 8.75,  'VA': 5.75, 'WA': 0.0,  'WV': 6.5,
    'WI': 7.65,  'WY': 0.0,   'DC': 10.75
}

# Function to run the TLH simulation
def run_tlh_simulation(asset_name, data, start_date, end_date, initial_investment, tlh_threshold, transaction_cost, tax_rate):
    # Ensure 'Date' column is in datetime format
    data['Date'] = pd.to_datetime(data['Date'])
    
    # Ensure start_date and end_date are in datetime format
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filter data by date range
    data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)].copy()
    
    # Check if the DataFrame is empty after filtering
    if data.empty:
        st.error(f"No data available for {asset_name} in the selected date range.")
        return None
    
    # Reset the index to ensure continuous indexing
    data.reset_index(drop=True, inplace=True)
    
    # Initialize columns
    data['Tax Benefit'] = 0.0
    data['Reinvested Units'] = 0.0
    data['Cost Basis'] = data['Close'].iloc[0]
    data['Units'] = initial_investment / data['Close'].iloc[0]
    data['TLH Portfolio Value'] = data['Units'] * data['Close']
    data['No TLH Portfolio Value'] = data['Units'] * data['Close']
    
    # TLH simulation loop
    for i in range(1, len(data)):
        if i - 1 < 0:  # Ensure valid indexing
            continue
        
        price_drop = (data.loc[i-1, 'Cost Basis'] - data.loc[i, 'Close']) / data.loc[i-1, 'Cost Basis']
        if price_drop >= tlh_threshold:
            capital_loss = (data.loc[i-1, 'Cost Basis'] - data.loc[i, 'Close']) * data.loc[i-1, 'Units']
            tax_benefit = capital_loss * tax_rate
            
            transaction_fee_initial = data.loc[i-1, 'Units'] * data.loc[i, 'Close'] * transaction_cost * 2
            reinvest_amount = tax_benefit - transaction_fee_initial
            transaction_fee_reinvestment = reinvest_amount * transaction_cost
            reinvest_amount_final = reinvest_amount - transaction_fee_reinvestment
            new_units = reinvest_amount_final / data.loc[i, 'Close']
            
            data.loc[i, 'Reinvested Units'] = new_units
            data.loc[i, 'Units'] = data.loc[i-1, 'Units'] + new_units
            data.loc[i, 'TLH Portfolio Value'] = data.loc[i, 'Units'] * data.loc[i, 'Close']
            data.loc[i, 'Cost Basis'] = data.loc[i, 'Close']
            data.loc[i, 'Tax Benefit'] = tax_benefit
        else:
            data.loc[i, 'Cost Basis'] = data.loc[i-1, 'Cost Basis']
            data.loc[i, 'Units'] = data.loc[i-1, 'Units']
            data.loc[i, 'TLH Portfolio Value'] = data.loc[i, 'Units'] * data.loc[i, 'Close']
        
        data.loc[i, 'No TLH Portfolio Value'] = data.loc[0, 'Units'] * data.loc[i, 'Close']
    
    # Calculate summary metrics
    summary_metrics = calculate_summary_with_rebalances(data)
    summary_metrics['Asset'] = asset_name
    return summary_metrics

# Function to calculate summary metrics
def calculate_summary_with_rebalances(data):
    initial_investment = 10000
    ending_investment_no_tlh = data['No TLH Portfolio Value'].iloc[-1]
    ending_investment_tlh = data['TLH Portfolio Value'].iloc[-1]

    num_days = (pd.to_datetime(data['Date'].iloc[-1]) - pd.to_datetime(data['Date'].iloc[0])).days
    num_years = num_days / 365.25

    annualized_return_no_tlh = ((ending_investment_no_tlh / initial_investment) ** (1 / num_years)) - 1
    annualized_return_tlh = ((ending_investment_tlh / initial_investment) ** (1 / num_years)) - 1

    tax_alpha = annualized_return_tlh - annualized_return_no_tlh

    summary_metrics = {
        "Initial Investment [$]": initial_investment,
        "Ending Investment (No TLH) [$]": ending_investment_no_tlh,
        "Ending Investment (With TLH) [$]": ending_investment_tlh,
        "Annualized Return (No TLH) [%]": annualized_return_no_tlh * 100,
        "Annualized Return (With TLH) [%]": annualized_return_tlh * 100,
        "Tax Alpha [%]": tax_alpha * 100,
        "Total Days": num_days,
        "Total Rebalances": data['Reinvested Units'].astype(bool).sum(),
        "Sum Total Tax Benefit [$]": data['Tax Benefit'].sum(),
        "Additional Units Purchased [Units]": data['Units'].iloc[-1] - data['Units'].iloc[0],
    }

    return summary_metrics

# Function to format the DataFrame
def format_dataframe(df):
    if df is None or df.empty:
        return df  # Return the DataFrame as is if it's None or empty
    
    formatted_df = df.copy()
    dollar_columns = ["Initial Investment [$]", "Ending Investment (No TLH) [$]", "Ending Investment (With TLH) [$]", "Sum Total Tax Benefit [$]"]
    percent_columns = ["Annualized Return (No TLH) [%]", "Annualized Return (With TLH) [%]", "Tax Alpha [%]"]
    units_columns = ["Additional Units Purchased [Units]"]

    for col in dollar_columns:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
    
    for col in percent_columns:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
    
    for col in units_columns:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.2f} units" if pd.notnull(x) else "N/A")

    if "Total Rebalances" in formatted_df.columns:
        formatted_df["Total Rebalances"] = formatted_df["Total Rebalances"].astype(int)
    
    return formatted_df

# Streamlit app setup
st.title("Tax Loss Harvesting Simulation")

# Load data for ETH, BTC, SPY
eth_data = pd.read_csv('ETH-daily.csv')
btc_data = pd.read_csv('BTC-daily.csv')
spy_data = pd.read_csv('SPY-daily.csv')

# Ensure 'Date' columns are in datetime format
eth_data['Date'] = pd.to_datetime(eth_data['Date'])
btc_data['Date'] = pd.to_datetime(btc_data['Date'])
spy_data['Date'] = pd.to_datetime(spy_data['Date'])

# Determine the earliest and latest dates across all datasets
min_date = max(eth_data['Date'].min(), btc_data['Date'].min(), spy_data['Date'].min())
max_date = min(eth_data['Date'].max(), btc_data['Date'].max(), spy_data['Date'].max())

# Set default parameters based on the data range
default_start_date = min_date
default_end_date = max_date
default_initial_investment = 10000
default_tlh_threshold = 0.01  # 1%
default_transaction_cost = 0.002  # 20 bps
default_federal_tax_rate = 20.0  # Default federal tax rate (you can adjust this as needed)

# Sidebar parameters for user customization
st.sidebar.header("Customize Simulation Parameters")

# State selection dropdown with default set to 'CA'
selected_state = st.sidebar.selectbox(
    "Select Your State", 
    list(state_tax_rates.keys()), 
    index=list(state_tax_rates.keys()).index('CA')
)
state_tax_rate = state_tax_rates[selected_state]
st.sidebar.write(f"State Tax Rate ({selected_state}): {state_tax_rate}%")

# Combine federal and state tax rates
combined_tax_rate = (default_federal_tax_rate + state_tax_rate) / 100
# Display selected tax rates
st.sidebar.write(f"Combined Tax Rate: {combined_tax_rate * 100:.2f}%")

# User adjustable parameters
start_date = st.sidebar.date_input("Start Date", value=default_start_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", value=default_end_date, min_value=min_date, max_value=max_date)
initial_investment = st.sidebar.number_input("Initial Investment ($)", value=default_initial_investment)
tlh_threshold = st.sidebar.slider("TLH Threshold (%)", 1, 5, value=int(default_tlh_threshold * 100), step=1) / 100  # Now an integer slider
transaction_cost = st.sidebar.slider("Transaction Cost (bps)", 1, 50, value=int(default_transaction_cost * 10000)) / 10000  # Convert to decimal

# Run the initial TLH simulation (based only on the date range and state)
initial_eth_summary = run_tlh_simulation('ETH', eth_data, default_start_date, default_end_date, default_initial_investment, default_tlh_threshold, default_transaction_cost, combined_tax_rate)
initial_btc_summary = run_tlh_simulation('BTC', btc_data, default_start_date, default_end_date, default_initial_investment, default_tlh_threshold, default_transaction_cost, combined_tax_rate)
initial_spy_summary = run_tlh_simulation('SPY', spy_data, default_start_date, default_end_date, default_initial_investment, default_tlh_threshold, default_transaction_cost, combined_tax_rate)

# Combine initial results into a DataFrame
initial_comparison_df = pd.DataFrame([initial_eth_summary, initial_btc_summary, initial_spy_summary])

# Ensure that the DataFrame is structured correctly
initial_comparison_df = initial_comparison_df.set_index('Asset').T

# Display the initial comparison results
st.subheader("Initial Comparison of TLH Performance")
st.write(f"Based on the defaults: Start Date: {default_start_date}, End Date: {default_end_date}, Initial Investment: ${default_initial_investment}, TLH Threshold: {default_tlh_threshold * 100}%, Transaction Cost: {default_transaction_cost * 10000} bps")
if not initial_comparison_df.empty:
    formatted_initial_comparison_df = format_dataframe(initial_comparison_df)
    st.write(formatted_initial_comparison_df)
else:
    st.write("No data available for the initial comparison.")

# Re-run TLH simulation based on all user parameters for the custom table
custom_eth_summary = run_tlh_simulation('ETH', eth_data, start_date, end_date, initial_investment, tlh_threshold, transaction_cost, combined_tax_rate)
custom_btc_summary = run_tlh_simulation('BTC', btc_data, start_date, end_date, initial_investment, tlh_threshold, transaction_cost, combined_tax_rate)
custom_spy_summary = run_tlh_simulation('SPY', spy_data, start_date, end_date, initial_investment, tlh_threshold, transaction_cost, combined_tax_rate)

# Combine custom results into a DataFrame
custom_comparison_df = pd.DataFrame([custom_eth_summary, custom_btc_summary, custom_spy_summary])

# Ensure that the DataFrame is structured correctly
custom_comparison_df = custom_comparison_df.set_index('Asset').T

# Display the custom comparison results
st.subheader("Custom Comparison of TLH Performance")
if not custom_comparison_df.empty:
    formatted_custom_comparison_df = format_dataframe(custom_comparison_df)
    st.write(formatted_custom_comparison_df)
else:
    st.write("No data available for the custom comparison.")
