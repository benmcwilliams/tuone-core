import ast
import pandas as pd

def clean_dataframe(df):
    """
    Cleans the DataFrame to standardize formats for comparison.
    - Converts stringified lists to actual lists.
    - Leaves scalar values unchanged.
    - Handles NaN values gracefully.
    """
    def safe_literal_eval(value):
        try:
            # Attempt to evaluate the string as a Python literal
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                return ast.literal_eval(value)
            return value
        except (ValueError, SyntaxError):
            # Return the original value if it cannot be parsed
            return value

    for col in df.columns:
        # Apply cleaning only to columns with stringified lists or mixed data
        df[col] = df[col].apply(safe_literal_eval)
    
    return df

def get_matching_projectIDs_with_comparison_excel(df1, df2, output_path):
    """
    Compare two DataFrames with identical columns and return a list of projectIDs
    where the rows match exactly across all columns. Also outputs an Excel file 
    showing matching and non-matching projects for manual review.

    Parameters:
        df1 (pd.DataFrame): First DataFrame.
        df2 (pd.DataFrame): Second DataFrame.
        output_path (str): Path to save the Excel file.

    Returns:
        list: List of matching projectIDs with identical rows.
    """
    # Define a placeholder for missing values
    placeholder = 'NA'
    
    # Define all values that indicate missing data
    missing_values = ['N/A', 'NA', 'Not disclosed', 'None', None, '', pd.NA, float('nan')]

    # Replace all missing values in both DataFrames
    df1.replace(missing_values, placeholder, inplace=True)
    df2.replace(missing_values, placeholder, inplace=True)

    # Merge the DataFrames on 'projectID' with an inner join
    merged_df = pd.merge(df1, df2, on='projectID', suffixes=('_df1', '_df2'))
    
    # Check for identical rows across all columns except 'projectID'
    merged_df['identical'] = (
        merged_df.filter(like='_df1').values == merged_df.filter(like='_df2').values
    ).all(axis=1)
    
    # Sort rows for easier comparison
    merged_df.sort_values(by=['identical', 'projectID'], ascending=[False, True], inplace=True)
    
    # Save to Excel for manual review
    with pd.ExcelWriter(output_path) as writer:
        merged_df.to_excel(writer, sheet_name='Comparison', index=False)
    
    # Extract matching projectIDs
    matching_projectIDs = merged_df.loc[merged_df['identical'], 'projectID'].tolist()
    
    return matching_projectIDs
