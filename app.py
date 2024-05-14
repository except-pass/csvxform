import pandas as pd
import streamlit as st

with st.sidebar:
    st.write("Version 0.0.3")

def reduce_df(df, columns_to_keep):
    for column in columns_to_keep:
        if column not in df.columns:
            st.warning(f"Didn't find the column '{column}'.  Did you upload the right file?")
            return None

    # Remove columns not in the list
    df = df.loc[:,columns_to_keep]
    return df

def ensure_numeric(df):
    for column in df.columns:
        if not pd.api.types.is_numeric_dtype(df[column]):
            st.error(f"This tool only works if the columns are numbers.  Check the '{column}' column.")
            return None
    return True

def process_df(df, program_id):
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    # Create a list of columns to keep
    columns_to_keep = ['Serial number', 'Time', 'vpv1', 'vpv2', 'vpv3', 'vBat', 'soc', 'ppv1', 'ppv2', 'ppv3', 'pCharge', 'pDisCharge', 'pinv', 'prec', 'pf', 'vepsr', 'vepss', 'vepst', 'feps', 'peps', 'seps', 'pToGrid', 'pToUser', 'pLoad']
    df = reduce_df(df, columns_to_keep)
    df['time_stamp'] = pd.to_datetime(df['Time'])
    df.set_index('time_stamp', inplace=True)
    df.drop('Time', axis=1, inplace=True)
    df['soc'] = df['soc'].str.replace('%', '').astype(int)

    if not ensure_numeric(df):
        return None, None
    # Resample to 15 minutes and average the cells
    df_resampled = df.resample('15min').mean()

    df_resampled['solar_power'] = df_resampled['ppv1'] + df_resampled['ppv2'] + df_resampled['ppv3']
    df_resampled['grid_power'] = df_resampled['pLoad'] 
    #charging is negative
    df_resampled['battery_power'] = -df_resampled['pCharge'] + df_resampled['pDisCharge']#create a new dataframe to just report the results
    result_df = df_resampled[['solar_power', 'battery_power', 'grid_power']]

    result_df.index = result_df.index.strftime('%Y/%m/%d %H:%M')

    serial_number = df['Serial number'].iloc[0]
    #result_df needs units of kW.  The original data is in W
    result_df = result_df / 1000
    return serial_number, result_df


if __name__ == "__main__":
    # Path to your file
    # Accept an uploaded file
    program_id = st.text_input("Enter the program ID", value="0001A")

    st.markdown("### Upload the xls that came from the Envy portal")
    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)


    if st.button("Or you can click here to use a sample file"):
        uploaded_files = ['before.xls']
    procedure = '''
    - Clean up the original dataframe
    - Resample to 15 minutes and average the cells
    - Name the index `time_stamp`
    - Create a new column 'solar_power' as the sum of 'ppv1', 'ppv2', and 'ppv3'
    - Create a new column 'grid_power' as the 'pLoad' column
    - Create a new column 'battery_power' as the sum of the values of 'pCharge' and 'pDisCharge'.  Charging is considered negative.
    - Convert the result to kW
    '''

    results ={}
    for uploaded_file in uploaded_files:
        if uploaded_file is not None:
            # Read the uploaded file into a pandas DataFrame
            df = pd.read_excel(uploaded_file)

            # Display the first few rows of the DataFrame to confirm
            st.markdown("## Original Data")
            st.dataframe(df)

            st.markdown(procedure)

            serial_number, result = process_df(df, program_id=program_id)
            if result is not None:
                st.markdown(f"## {serial_number} Processed")
                result = result.rename(columns=lambda x: f"{serial_number}_{x}")
                result['program_id'] = program_id

                st.dataframe(result)
                #results[serial_number] = result.rename(columns=lambda x: f"{serial_number}_{x}")
                results[serial_number] = result
            

    if results:
        master_df = pd.concat(results.values(), axis=1)
        st.markdown("## Master Results")
        st.dataframe(master_df)

        total_battery_power = master_df.filter(like='_battery_power').sum(axis=1)
        total_solar_power = master_df.filter(like='_solar_power').sum(axis=1)
        total_grid_power = master_df.filter(like='_grid_power').sum(axis=1)


        total_df = pd.DataFrame({'program_id': master_df['program_id'],
                                 'total_solar_power': total_solar_power.round(3),
                                 'total_battery_power': total_battery_power.round(3),
                                 'total_grid_power': total_grid_power.round(3)
                                }, index=master_df.index)
        
        st.markdown("## DF that sums the powers")
        st.dataframe(total_df)