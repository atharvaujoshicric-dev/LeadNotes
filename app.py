import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Lead & Notes Analytics")

st.title("📊 Lead and Notes Mapping App")

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
    
    # 1. Pipeline Stage Table
    st.subheader("📍 Pipeline Stage Distribution")
    pipeline_counts = leads_df['Pipeline Stage'].value_counts().reset_index()
    pipeline_counts.columns = ['Pipeline Stage', 'Count']
    st.table(pipeline_counts)
    
    # 2. Unqualified Reason Table
    st.subheader("❌ Unqualified Reason Distribution")
    reason_counts = leads_df['Pipeline Stage Reason'].value_counts().reset_index()
    reason_counts.columns = ['Reason', 'Count']
    st.table(reason_counts)
    
    # 3. Text Summary
    st.subheader("📝 Unqualification Summary")
    total_unq = reason_counts['Count'].sum()
    top_reason = reason_counts.iloc[0]['Reason']
    top_perc = (reason_counts.iloc[0]['Count'] / total_unq) * 100
    
    summary = f"""
    The data shows a total of **{total_unq}** unqualified leads. 
    The most frequent reason is **'{top_reason}'**, which accounts for **{top_perc:.1f}%** of all disqualifications.
    """
    st.info(summary)
    
    # 4. Mapped Table (Leads & Notes)
    st.subheader("🔗 Leads and Notes Mapping")
    merged_df = pd.merge(
        leads_df[['id', 'Full Name', 'Pipeline Stage', 'Pipeline Stage Reason', 'Phone Numbers']], 
        notes_df[['Associated entity id', 'Content', 'Created At']], 
        left_on='id', right_on='Associated entity id', how='left'
    ).drop(columns=['Associated entity id'])
    
    # Simulate "Merge and Center" by setting repeated names to empty for display
    display_df = merged_df.copy()
    display_df['Full Name'] = display_df['Full Name'].mask(display_df['Full Name'].duplicated(), "")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Download Button
    csv = merged_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Mapped Data CSV", csv, "Mapped_Leads_Notes.csv", "text/csv")

else:
    st.warning("Please upload both the Leads and Notes CSV files to proceed.")
