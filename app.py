import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Page Configuration
st.set_page_config(
    page_title="Healthcare Performance Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    .main { padding: 1rem; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Data Loading & Generation Helper
# ---------------------------------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("healthcare_data.csv")
    except FileNotFoundError:
        # Fallback dataset generator if local file is missing
        np.random.seed(42)
        n = 300
        departments = ['Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics', 'Oncology']
        insurance = ['Medicare', 'Private', 'Medicaid', 'Uninsured']
        
        df = pd.DataFrame({
            'Patient_ID': [f'P-{1000+i}' for i in range(n)],
            'Age': np.random.randint(18, 85, n),
            'Gender': np.random.choice(['Male', 'Female'], n),
            'Department': np.random.choice(departments, n),
            'Insurance_Provider': np.random.choice(insurance, n),
            'Length_of_Stay_Days': np.random.poisson(lam=5, size=n) + 1,
            'Billing_Amount_USD': np.random.uniform(2000, 45000, n).round(2),
            'Readmitted': np.random.choice(['Yes', 'No'], n, p=[0.2, 0.8])
        })
        df.to_csv("healthcare_data.csv", index=False)
    return df

data = load_data()

# ---------------------------------------------------------
# Sidebar - User Interactive Controls
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/hospital-2.png", width=80)
st.sidebar.title("Navigation & Filters")

# Navigation Menu
page = st.sidebar.radio("Go to Page", ["🏠 Home / Overview", "📊 Department Analysis", "🔮 Patient Estimator"])

st.sidebar.markdown("---")
st.sidebar.header("Global Filters")

# Multiselect Widget
selected_depts = st.sidebar.multiselect(
    "Filter by Department",
    options=list(data['Department'].unique()),
    default=list(data['Department'].unique())
)

# Slider Widget
age_range = st.sidebar.slider(
    "Select Patient Age Range",
    min_value=int(data['Age'].min()),
    max_value=int(data['Age'].max()),
    value=(int(data['Age'].min()), int(data['Age'].max()))
)

# Filter Dataset based on Widget Inputs
filtered_df = data[
    (data['Department'].isin(selected_depts)) & 
    (data['Age'].between(age_range[0], age_range[1]))
]

# ---------------------------------------------------------
# Page 1: Home / Overview
# ---------------------------------------------------------
if page == "🏠 Home / Overview":
    st.title("🏥 Hospital Performance & Patient Metrics")
    st.caption("Interactive analytics platform for regional healthcare monitoring.")
    st.markdown("---")

    # High-level Metrics Section
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Admissions", f"{len(filtered_df)}")
    col2.metric("Avg Length of Stay", f"{filtered_df['Length_of_Stay_Days'].mean():.1f} Days")
    col3.metric("Total Revenue Generated", f"${filtered_df['Billing_Amount_USD'].sum():,.2f}")
    
    readmit_rate = (filtered_df['Readmitted'].value_counts(normalize=True).get('Yes', 0)) * 100
    col4.metric("30-Day Readmission Rate", f"{readmit_rate:.1f}%")

    st.markdown("---")

    # Charts Section
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Billing Amount Distribution by Department")
        fig_box = px.box(
            filtered_df, 
            x="Department", 
            y="Billing_Amount_USD", 
            color="Department",
            points="all",
            title="Billing Outliers & Spread"
        )
        st.plotly_chart(fig_box, use_container_width=True)

    with c2:
        st.subheader("Admissions by Insurance Provider")
        fig_pie = px.pie(
            filtered_df, 
            names="Insurance_Provider", 
            title="Insurance Coverage Breakdown",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Raw Data View")
    with st.expander("Click to view filtered patient records"):
        st.dataframe(filtered_df)

# ---------------------------------------------------------
# Page 2: Department Analysis
# ---------------------------------------------------------
elif page == "📊 Department Analysis":
    st.title("📊 Department Level Metrics")
    st.markdown("---")

    # Interactive Selectbox
    selected_dept = st.selectbox("Select Specific Department to Inspect", options=data['Department'].unique())
    dept_df = filtered_df[filtered_df['Department'] == selected_dept]

    if dept_df.empty:
        st.warning("No data available with current sidebar filter settings.")
    else:
        st.subheader(f"Metrics for {selected_dept}")
        
        fig_scatter = px.scatter(
            dept_df,
            x="Age",
            y="Billing_Amount_USD",
            size="Length_of_Stay_Days",
            color="Readmitted",
            hover_data=["Patient_ID"],
            title=f"Age vs. Billing Amount (Bubble size = Length of Stay)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig_hist = px.histogram(dept_df, x="Length_of_Stay_Days", nbins=10, title="Length of Stay Distribution")
            st.plotly_chart(fig_hist, use_container_width=True)
        with col2:
            gender_counts = dept_df['Gender'].value_counts().reset_index()
            fig_bar = px.bar(gender_counts, x='Gender', y='count', title='Gender Demographics')
            st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------
# Page 3: Patient Estimator (Interactive Tool)
# ---------------------------------------------------------
elif page == "🔮 Patient Estimator":
    st.title("🔮 Interactive Cost & Stay Estimator")
    st.write("Calculate estimated hospital costs based on patient demographic parameters.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        est_age = st.number_input("Patient Age", min_value=1, max_value=100, value=45)
        est_dept = st.selectbox("Target Department", options=data['Department'].unique())
        est_stay = st.slider("Anticipated Days of Stay", min_value=1, max_value=30, value=5)
    
    with col2:
        est_ins = st.selectbox("Insurance Provider", options=data['Insurance_Provider'].unique())
        is_readmit = st.checkbox("Has previous readmission history?")

    # Simple Rule-based estimation logic for demonstration
    base_rate = 1500
    dept_multipliers = {'Cardiology': 2.1, 'Neurology': 2.3, 'Orthopedics': 1.8, 'Pediatrics': 1.2, 'Oncology': 2.5}
    
    estimated_cost = (est_stay * base_rate * dept_multipliers.get(est_dept, 1.0))
    if is_readmit:
        estimated_cost *= 1.15

    st.markdown("---")
    st.subheader("Estimation Result")
    st.success(f"Estimated Total Billing Cost: **${estimated_cost:,.2f} USD**")