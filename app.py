import pandas as pd
import streamlit as st



def process_df(df):
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    # Create a list of columns to keep
    columns_to_keep = ['Serial number', 'Time', 'vpv1', 'vpv2', 'vpv3', 'vBat', 'soc', 'ppv1', 'ppv2', 'ppv3', 'pCharge', 'pDisCharge', 'pinv', 'prec', 'pf', 'vepsr', 'vepss', 'vepst', 'feps', 'peps', 'seps', 'pToGrid', 'pToUser', 'pLoad']
    for column in columns_to_keep:
        if column not in df.columns:
            st.warning(f"Didn't find the column '{column}'.  Did you upload the right file?")
            return None

    # Remove columns not in the list
    df = df[columns_to_keep]
    df['Time'] = pd.to_datetime(df['Time'])
    df.set_index('Time', inplace=True)
    df['soc'] = df['soc'].str.replace('%', '').astype(int)
    # Resample to 15 minutes and average the cells
    df_resampled = df.resample('15min').mean()

    df_resampled['solar_power'] = df_resampled['ppv1'] + df_resampled['ppv2'] + df_resampled['ppv3']
    df_resampled['grid_power'] = df_resampled['pLoad'] 
    #charging is negative
    df_resampled['battery_power'] = -df_resampled['pCharge'] + df_resampled['pDisCharge']#create a new dataframe to just report the results
    result_df = df_resampled[['solar_power', 'battery_power', 'grid_power']]

    result_df.index = result_df.index.strftime('%Y/%m/%d %H:%M')


    #result_df needs units of kW.  The original data is in W
    result_df = result_df / 1000
    return result_df


if __name__ == "__main__":
    # Path to your file
    # Accept an uploaded file
    st.markdown("### Upload the xls that came from the Envy portal")
    uploaded_file = st.file_uploader("Upload a file")


    if st.button("Or you can click here to use a sample file"):
        uploaded_file = 'before.xls'
    procedure = '''
    - Clean up the original dataframe
    - Resample to 15 minutes and average the cells
    - Name the index `time_stamp`
    - Create a new column 'solar_power' as the sum of 'ppv1', 'ppv2', and 'ppv3'
    - Create a new column 'grid_power' as the 'pLoad' column
    - Create a new column 'battery_power' as the sum of the absolute values of 'pCharge' and 'pDisCharge'
    - Convert the result to kW
    '''

    if uploaded_file is not None:
        # Read the uploaded file into a pandas DataFrame
        df = pd.read_excel(uploaded_file)

        # Display the first few rows of the DataFrame to confirm
        st.markdown("## Original Data")
        st.dataframe(df)

        st.markdown(procedure)

        result = process_df(df)
        if result is not None:
            st.markdown("## Processed Data")
            st.dataframe(result)