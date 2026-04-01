import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide", page_title="Lead & Notes Analytics Pro")

st.title("📊 Lead and Notes Excel Generator")

# File Uploaders
col1, col2 = st.columns(2)
with col1:
    leads_file = st.file_uploader("Upload Leads CSV", type="csv")
with col2:
    notes_file = st.file_uploader("Upload Notes CSV", type="csv")

if leads_file and notes_file:
    # 1. Load Data
    leads_df = pd.read_csv(leads_file)
    notes_df = pd.read_csv(notes_file)
    
    # 2. Pre-processing
    leads_df['Full Name'] = leads_df['First Name'].fillna('') + ' ' + leads_df['Last Name'].fillna('')
    leads_df['Full Name'] = leads_df['Full Name'].str.strip()
    leads_df['id'] = leads_df['id'].astype(str)
    notes_df['Associated entity id'] = notes_df['Associated entity id'].astype(str)
    
    # Rename for the mapping sheet
    notes_df = notes_df.rename(columns={'Content': 'Notes', 'Created At': 'Note Created At'})
    
    # 3. Merge Data for Mapping
    # User requested sequence: id, Full name, Phone Numbers, Created At, Pipeline Stage Reason, Notes
    # We include Pipeline Stage as well because it was requested to be merged.
    mapping_df = pd.merge(
        leads_df[['id', 'Full Name', 'Phone Numbers', 'Pipeline Stage', 'Pipeline Stage Reason']], 
        notes_df[['Associated entity id', 'Notes', 'Note Created At']], 
        left_on='id', right_on='Associated entity id', how='left'
    ).drop(columns=['Associated entity id'])

    # Reorder columns as requested
    mapping_df = mapping_df[['id', 'Full Name', 'Phone Numbers', 'Pipeline Stage', 'Note Created At', 'Pipeline Stage Reason', 'Notes']]
    mapping_df = mapping_df.sort_values(by='id').reset_index(drop=True)
    
    # 4. Generate Summaries
    pipeline_counts = leads_df['Pipeline Stage'].value_counts().reset_index()
    pipeline_counts.columns = ['Pipeline Stage', 'Count']
    
    reason_counts = leads_df['Pipeline Stage Reason'].value_counts().reset_index()
    reason_counts.columns = ['Unqualified Reason', 'Count']

    # 5. Create Excel with Multiple Sheets and Merged Cells
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        mapping_df.to_excel(writer, sheet_name='Mapping', index=False)
        reason_counts.to_excel(writer, sheet_name='Unqualified Reasons Count', index=False)
        pipeline_counts.to_excel(writer, sheet_name='Pipeline Stage Count', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Mapping']
        
        # Formatting for Merge and Center
        merge_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True
        })
        
        # Columns to Merge: id (0), Full Name (1), Phone Numbers (2), Pipeline Stage (3)
        df = mapping_df
        rows = len(df)
        cols_to_merge = [0, 1, 2, 3] 

        for col_idx in cols_to_merge:
            i = 0
            while i < rows:
                j = i + 1
                # Check if subsequent rows match the lead ID and the current column value
                while j < rows and str(df.iloc[j, col_idx]) == str(df.iloc[i, col_idx]) and str(df.iloc[j, 0]) == str(df.iloc[i, 0]):
                    j += 1
                
                val = df.iloc[i, col_idx]
                if pd.isna(val): val = ""
                
                if j - i > 1:
                    worksheet.merge_range(i + 1, col_idx, j, col_idx, val, merge_format)
                else:
                    worksheet.write(i + 1, col_idx, val, merge_format)
                i = j
                
    # UI Section
    st.subheader("⬇️ Download Final Report")
    st.download_button(
        label="Download Leads_Analytics_Report.xlsx",
        data=output.getvalue(),
        file_name="Leads_Analytics_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 6. Display Text Summary
    st.divider()
    total_unq = reason_counts['Count'].sum()
    top_reason = reason_counts.iloc[0]['Unqualified Reason']
    top_perc = (reason_counts.iloc[0]['Count'] / total_unq) * 100
    st.markdown(f"**Analysis Summary:** A total of **{total_unq}** leads were unqualified. The primary reason is **'{top_reason}'**, accounting for **{top_perc:.1f}%** of the lost opportunities.")

else:
    st.info("Please upload both the Leads and Notes CSV files.")
