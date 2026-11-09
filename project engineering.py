import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. PAGE CONFIG & FRONTEND MEMORY (STORAGE)
# ==========================================
st.set_page_config(page_title="Reactor Material Balance", layout="wide")

# Initialize frontend storage to remember user inputs across steps
if 'Nc' not in st.session_state: st.session_state.Nc = 3
if 'Nin' not in st.session_state: st.session_state.Nin = 2
if 'Nout' not in st.session_state: st.session_state.Nout = 1
if 'Nr' not in st.session_state: st.session_state.Nr = 1

# Store DataFrames dynamically
if 'species_df' not in st.session_state:
    st.session_state.species_df = pd.DataFrame({"Species Name": ['A', 'B', 'C']})
if 'in_streams_df' not in st.session_state:
    st.session_state.in_streams_df = pd.DataFrame({"Stream ID": ['Feed 1', 'Feed 2'], "Type": ['Input', 'Input']})
if 'out_streams_df' not in st.session_state:
    st.session_state.out_streams_df = pd.DataFrame({"Stream ID": ['Product 1'], "Type": ['Output']})
if 'stoich_df' not in st.session_state:
    st.session_state.stoich_df = pd.DataFrame(np.zeros((1, 3)), columns=['A', 'B', 'C'], index=['Reaction 1'])

# ==========================================
# 2. SIDEBAR WIZARD NAVIGATION
# ==========================================
st.sidebar.title("🎛️ Setup Wizard")
menu = [
    "1. System Specification", 
    "2. Species Definition", 
    "3. Streams Definition", 
    "4. Reaction Specification", 
    "5. Data Entry & Solve"
]
step = st.sidebar.radio("Navigate Steps:", menu)

# ==========================================
# 3. INTERFACE SCREENS WITH DATA STORAGE
# ==========================================

if step == "1. System Specification":
    st.header("1. System Specification")
    st.write("Specify the number of variables. The frontend will adapt automatically.[cite: 1, 3]")
    
    col1, col2 = st.columns(2)
    with col1:
        # User specifies values; Streamlit stores them in session_state automatically via 'key'
        st.number_input("Number of Species (Nc)", min_value=1, max_value=10, key="Nc")
        st.number_input("Number of Input Streams (Nin)", min_value=1, max_value=5, key="Nin")
        st.number_input("Number of Output Streams (Nout)", min_value=1, max_value=5, key="Nout")
        st.number_input("Number of Reactions (Nr)", min_value=0, max_value=5, key="Nr")
        
    with col2:
        st.info("💡 **Tip:** Changing these numbers will automatically resize the input tables in the next steps while preserving your entered data where possible.")

elif step == "2. Species Definition":
    st.header("2. Species Definition")
    st.write("Name your chemical species. These names will be stored and used in later steps.")
    
    # Adjust dataframe size based on Step 1
    current_len = len(st.session_state.species_df)
    if st.session_state.Nc > current_len:
        new_rows = pd.DataFrame({"Species Name": [f"Sp_{i+1}" for i in range(current_len, st.session_state.Nc)]})
        st.session_state.species_df = pd.concat([st.session_state.species_df, new_rows], ignore_index=True)
    elif st.session_state.Nc < current_len:
        st.session_state.species_df = st.session_state.species_df.iloc[:st.session_state.Nc]

    # Data Editor: Captures user input and stores it back into session state
    st.session_state.species_df = st.data_editor(st.session_state.species_df, use_container_width=True, num_rows="fixed")

elif step == "3. Streams Definition":
    st.header("3. Stream Definition")
    st.write("Define your stream names.[cite: 3]")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Streams")
        # Resize input streams df
        if st.session_state.Nin != len(st.session_state.in_streams_df):
            st.session_state.in_streams_df = pd.DataFrame({
                "Stream ID": [f"Feed {i+1}" for i in range(st.session_state.Nin)],
                "Type": ["Input" for _ in range(st.session_state.Nin)]
            })
        st.session_state.in_streams_df = st.data_editor(st.session_state.in_streams_df, use_container_width=True)
        
    with col2:
        st.subheader("Output Streams")
        # Resize output streams df
        if st.session_state.Nout != len(st.session_state.out_streams_df):
            st.session_state.out_streams_df = pd.DataFrame({
                "Stream ID": [f"Product {i+1}" for i in range(st.session_state.Nout)],
                "Type": ["Output" for _ in range(st.session_state.Nout)]
            })
        st.session_state.out_streams_df = st.data_editor(st.session_state.out_streams_df, use_container_width=True)

elif step == "4. Reaction Specification":
    st.header("4. Reaction Specification")
    if st.session_state.Nr == 0:
        st.success("No reactions specified. System is physical only.")
    else:
        st.write("Specify stoichiometric coefficients (-ve for reactants, +ve for products).[cite: 1, 3]")
        
        species_list = st.session_state.species_df["Species Name"].tolist()
        
        # Build matrix dynamically based on user's stored species and reaction counts
        if list(st.session_state.stoich_df.columns) != species_list or len(st.session_state.stoich_df) != st.session_state.Nr:
            st.session_state.stoich_df = pd.DataFrame(
                np.zeros((st.session_state.Nr, st.session_state.Nc)), 
                columns=species_list, 
                index=[f"Reaction {i+1}" for i in range(st.session_state.Nr)]
            )
        
        # Store user entries for stoichiometry
        st.session_state.stoich_df = st.data_editor(st.session_state.stoich_df, use_container_width=True)

elif step == "5. Data Entry & Solve":
    st.header("5. Data Entry & Solver")
    st.write("Enter flow rates and compositions. Columns and rows are fetched from your previous inputs.")
    
    species_list = st.session_state.species_df["Species Name"].tolist()
    in_stream_names = st.session_state.in_streams_df["Stream ID"].tolist()
    
    # Initialize the input data table if it doesn't match the current dimensions
    cols = ["Total Flow (mol/h)"] + [f"x_{sp}" for sp in species_list]
    
    if 'feed_data_df' not in st.session_state or list(st.session_state.feed_data_df.columns) != cols or list(st.session_state.feed_data_df.index) != in_stream_names:
        st.session_state.feed_data_df = pd.DataFrame(np.zeros((st.session_state.Nin, len(cols))), columns=cols, index=in_stream_names)
    
    # Frontend table for user to specify flows/fractions
    st.session_state.feed_data_df = st.data_editor(st.session_state.feed_data_df, use_container_width=True)
    
    st.markdown("---")
    if st.button("🚀 Calculate Material Balance", type="primary"):
        st.success("Data successfully stored and retrieved for calculation!")
        
        # Display the collected data to prove it is stored in the frontend
        st.write("### Stored Frontend Data Ready for Solver:")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Stoichiometry Matrix:**")
            st.dataframe(st.session_state.stoich_df, use_container_width=True)
        with col2:
            st.write("**Inlet Stream Conditions:**")
            st.dataframe(st.session_state.feed_data_df, use_container_width=True)
        
        # Mock calculation output matching the dashboard design[cite: 4]
        st.subheader("Calculation Results")
        res1, res2 = st.columns(2)
        res1.metric("Total In", f"{st.session_state.feed_data_df['Total Flow (mol/h)'].sum()} mol/h")
        res2.metric("Total Out", f"{st.session_state.feed_data_df['Total Flow (mol/h)'].sum()} mol/h")
        