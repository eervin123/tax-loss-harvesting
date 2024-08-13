import pandas as pd

# Function to run the TLH simulation
def run_tlh_simulation(asset_name, data, start_date, end_date, initial_investment, tlh_threshold, transaction_cost, tax_rate):
    data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)].copy()
    
    # Initialize columns
    data['Tax Benefit'] = 0.0
    data['Reinvested Shares'] = 0.0
    data['Cost Basis'] = data['Close'].iloc[0]
    data['Shares'] = initial_investment / data['Close'].iloc[0]
    data['TLH Portfolio Value'] = data['Shares'] * data['Close']
    data['No TLH Portfolio Value'] = data['Shares'] * data['Close']
    
    # TLH simulation loop
    for i in range(1, len(data)):
        price_drop = (data.loc[i-1, 'Cost Basis'] - data.loc[i, 'Close']) / data.loc[i-1, 'Cost Basis']
        if price_drop >= tlh_threshold:
            capital_loss = (data.loc[i-1, 'Cost Basis'] - data.loc[i, 'Close']) * data.loc[i-1, 'Shares']
            tax_benefit = capital_loss * tax_rate
            
            transaction_fee_initial = data.loc[i-1, 'Shares'] * data.loc[i, 'Close'] * transaction_cost * 2
            reinvest_amount = tax_benefit - transaction_fee_initial
            transaction_fee_reinvestment = reinvest_amount * transaction_cost
            reinvest_amount_final = reinvest_amount - transaction_fee_reinvestment
            new_shares = reinvest_amount_final / data.loc[i, 'Close']
            
            data.loc[i, 'Reinvested Shares'] = new_shares
            data.loc[i, 'Shares'] = data.loc[i-1, 'Shares'] + new_shares
            data.loc[i, 'TLH Portfolio Value'] = data.loc[i, 'Shares'] * data.loc[i, 'Close']
            data.loc[i, 'Cost Basis'] = data.loc[i, 'Close']
            data.loc[i, 'Tax Benefit'] = tax_benefit
        else:
            data.loc[i, 'Cost Basis'] = data.loc[i-1, 'Cost Basis']
            data.loc[i, 'Shares'] = data.loc[i-1, 'Shares']
            data.loc[i, 'TLH Portfolio Value'] = data.loc[i, 'Shares'] * data.loc[i, 'Close']
        
        data.loc[i, 'No TLH Portfolio Value'] = data.loc[0, 'Shares'] * data.loc[i, 'Close']
    
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
        "Initial Investment": initial_investment,
        "Ending Investment (No TLH)": ending_investment_no_tlh,
        "Ending Investment (With TLH)": ending_investment_tlh,
        "Annualized Return (No TLH)": annualized_return_no_tlh * 100,
        "Annualized Return (With TLH)": annualized_return_tlh * 100,
        "Tax Alpha": tax_alpha * 100,
        "Total Days": num_days,
        "Total Rebalances": data['Reinvested Shares'].astype(bool).sum(),
        "Sum Total Tax Benefit Reinvested": data['Tax Benefit'].sum(),
        "Additional Shares Purchased": data['Shares'].iloc[-1] - data['Shares'].iloc[0],
    }

    return summary_metrics

# Load data for ETH, BTC, SPY
eth_data = pd.read_csv('ETH-daily.csv')
btc_data = pd.read_csv('BTC-daily.csv')
spy_data = pd.read_csv('SPY-daily.csv')

# Set parameters
start_date = '2019-01-01'
end_date = '2024-12-31'
initial_investment = 10000
tlh_threshold = 0.03  # 5% drop
transaction_cost = 0.002  # 20 bps per side
tax_rate = 0.333

# Run TLH simulation for each asset
eth_summary = run_tlh_simulation('ETH', eth_data, start_date, end_date, initial_investment, tlh_threshold, transaction_cost, tax_rate)
btc_summary = run_tlh_simulation('BTC', btc_data, start_date, end_date, initial_investment, tlh_threshold, transaction_cost, tax_rate)
spy_summary = run_tlh_simulation('SPY', spy_data, start_date, end_date, initial_investment, tlh_threshold, transaction_cost, tax_rate)

# Combine results into a DataFrame
comparison_df = pd.DataFrame([eth_summary, btc_summary, spy_summary])

# Transpose the DataFrame for better readability
transposed_df = comparison_df.T

# Name the columns as the asset names
columns = comparison_df['Asset']
transposed_df.columns = columns

# Remove the 'Asset' column
transposed_df = transposed_df.drop('Asset')

# Ensure all columns are numeric before rounding
numeric_cols = transposed_df.select_dtypes(include='number').columns
transposed_df[numeric_cols] = transposed_df[numeric_cols].apply(pd.to_numeric)

# Round all of the column values to 2 decimal places and print the DataFrame
print(transposed_df.round(2))