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
    # Load Data
    leads_df = pd.read_csv(leads_file)
    notes_df = pd.read_csv(notes_file)
    
    # Pre-processing
    leads_df['Full Name'] = leads_df['First Name'].fillna('') + ' ' + leads_df['Last Name'].fillna('')
    leads_df['Full Name'] = leads_df['Full Name'].str.strip()
    leads_df['id'] = leads_df['id'].astype(str)
    notes_df['Associated entity id'] = notes_df['Associated entity id'].astype(str)
    
    # 1. Prepare Dataframes
    # Mapping
    mapping_df = pd.merge(
        leads_df[['id', 'Full Name', 'Pipeline Stage', 'Pipeline Stage Reason', 'Phone Numbers']], 
        notes_df[['Associated entity id', 'Content', 'Created At']], 
        left_on='id', right_on='Associated entity id', how='left'
    ).drop(columns=['Associated entity id']).sort_values(by='id').reset_index(drop=True)
    
    # Counts
    pipeline_counts = leads_df['Pipeline Stage'].value_counts().reset_index()
    pipeline_counts.columns = ['Pipeline Stage', 'Count']
    
    reason_counts = leads_df['Pipeline Stage Reason'].value_counts().reset_index()
    reason_counts.columns = ['Unqualified Reason', 'Count']

    # 2. Display Preview in App
    st.subheader("📍 Pipeline Stage Distribution")
    st.table(pipeline_counts)
    
    st.subheader("❌ Unqualified Reason Distribution")
    st.table(reason_counts)

    # 3. Create Excel with Multiple Sheets and Merged Cells
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write Dataframes to sheets
        mapping_df.to_excel(writer, sheet_name='Mapping', index=False)
        reason_counts.to_excel(writer, sheet_name='Unqualified Reasons Count', index=False)
        pipeline_counts.to_excel(writer, sheet_name='Pipeline Stage Count', index=False)
        
        # Access xlsxwriter objects
        workbook = writer.book
        worksheet = writer.sheets['Mapping']
        
        # Formatting for Merge and Center
        merge_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        # Merge logic for ID and Full Name
        df = mapping_df
        rows = len(df)
        for col_idx in [0, 1]: # Columns: id and Full Name
            i = 0
            while i < rows:
                j = i + 1
                while j < rows and df.iloc[j, col_idx] == df.iloc[i, col_idx]:
                    j += 1
                if j - i > 1:
                    worksheet.merge_range(i + 1, col_idx, j, col_idx, df.iloc[i, col_idx], merge_format)
                else:
                    worksheet.write(i + 1, col_idx, df.iloc[i, col_idx], merge_format)
                i = j
                
    st.subheader("⬇️ Download Formatted Excel")
    st.download_button(
        label="Download Leads_Analytics_Report.xlsx",
        data=output.getvalue(),
        file_name="Leads_Analytics_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 4. Text Summary
    st.divider()
    total_unq = reason_counts['Count'].sum()
    top_reason = reason_counts.iloc[0]['Unqualified Reason']
    top_perc = (reason_counts.iloc[0]['Count'] / total_unq) * 100
    st.markdown(f"**Unqualification Summary:** {total_unq} leads were unqualified. The top reason is **{top_reason}** ({top_perc:.1f}%).")

else:
    st.info("Upload the CSV files to generate the multi-sheet Excel report.")
