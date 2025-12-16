import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Health Performance Dashboard - MoH",
    page_icon="",
    layout="wide"
)

# --- PAGE CONFIGURATION ---
st.title("Tableau de Bord de Performance Sanitaire")
st.markdown("""
This dashboard allows you to view key performance indicators (KPIs) for healthcare facilities
based on clinical, governance, and operational data..
""")

# --- DATA LOADING FUNCTION ---
@st.cache_data # help to cache data loading for performance
def load_data():
    # CSV file loading (with error handling) - ensure the files are in the same directory
    try:
        facilities = pd.read_csv('facilities.csv')
        clinical = pd.read_csv('clinical_neonatal.csv')
        governance = pd.read_csv('governance.csv')
        operations = pd.read_csv('operations.csv')
        return facilities, clinical, governance, operations
    except FileNotFoundError:
        st.error("Erreur : Fichiers CSV introuvables. Vérifiez qu'ils sont bien dans le dossier.")
        return None, None, None, None

# Function call to load data
facilities_df, clinical_df, governance_df, operations_df = load_data()

if facilities_df is not None:

    # --- MÉTRIC 1 : GOUVERNANCE (New born protocol) ---
    # "top facilities by governance criteria (newborn_protocol_exists)"
    
    st.header("1. Gouvernance & Compliance")
    st.info("Criterion analyzed: Existence of a care protocol for newborns.")

    # Fusion of dataframes to get necessary info (facility and Governance)
    gov_merged = pd.merge(facilities_df, governance_df, on='facility_id')

    # Reaprtition calcul  (Combien ont 'Yes', 'No', 'Outdated')
    protocol_counts = gov_merged['newborn_protocol_exists'].value_counts().reset_index()
    protocol_counts.columns = ['Statut du Protocole', 'Nombre de Structures']

    # Creation of two columns  (Graphique on left , Table on right)
    col1, col2 = st.columns([1, 1])

    with col1:
        # Graphique Camembert (Pie Chart) withPlotly
        fig_gov = px.pie(
            protocol_counts, 
            values='Nombre de Structures', 
            names='Statut du Protocole',
            title='Répartition des Protocoles Nouveau-nés',
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_gov, use_container_width=True)

    with col2:
        # Display of “Top Facilities” (Those that are compliant ‘Yes’)
        st.subheader("List of compliant structures (Top Tier)")
        compliant_facilities = gov_merged[gov_merged['newborn_protocol_exists'] == 'Yes'][
            ['facility_name', 'district', 'tier_level']
        ]
        st.dataframe(compliant_facilities, height=300)

    # --- MÉTRIC 2 : MATERNAL INDICATORS (Live Births) ---

    st.markdown("---") # Separation line
    st.header("2. Clinical Indicators (Maternity)")
    
    # Aggregation of live births by month
    # First, convert the date column.
    clinical_df['reporting_month'] = pd.to_datetime(clinical_df['reporting_month'])
    
    # Group by Month to see the time trend
    monthly_trend = clinical_df.groupby('reporting_month')['live_births'].sum().reset_index()

    # Trend Chart (Line Chart)
    fig_clinical = px.line(
        monthly_trend, 
        x='reporting_month', 
        y='live_births', 
        markers=True,
        title='Trends in Live Births (2024)',
        labels={'reporting_month': 'Month', 'live_births': 'Nombre de Naissances'}
    )
    st.plotly_chart(fig_clinical, use_container_width=True)

    #  Analysis by District (Merge with facilities to obtain the district)
    clinical_merged = pd.merge(clinical_df, facilities_df[['facility_id', 'district']], on='facility_id')
    district_births = clinical_merged.groupby('district')['live_births'].sum().reset_index().sort_values(by='live_births', ascending=False)
    
    # Bar Chart by District
    fig_district = px.bar(
        district_births,
        x='district',
        y='live_births',
        title='Number of Births by District (Total)',
        color='live_births',
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig_district, use_container_width=True)

    # --- MÉTRIC 3 : OPERATIONAL PERFORMANCE (Oxygen) ---


    st.markdown("---")
    st.header("3. Availability of Critical Resources (Oxygen)")

    # Fusion Facilities + Operations dataframes
    ops_merged = pd.merge(facilities_df, operations_df, on='facility_id')

    # Selection of the top 10 facilities with the most oxygen cylinders
    ops_merged['oxygen_cylinders_available'] = pd.to_numeric(ops_merged['oxygen_cylinders_available'], errors='coerce').fillna(0)
    
    top_oxygen = ops_merged.sort_values(by='oxygen_cylinders_available', ascending=False).head(15)

    # Graphique en Barres horizontal
    fig_ops = px.bar(
        top_oxygen,
        x='oxygen_cylinders_available',
        y='facility_name',
        orientation='h', # Barres horizontales pour lire les noms
        title='Top 15 Structures by Oxygen Availability',
        labels={'oxygen_cylinders_available': 'Number of Bottles', 'facility_name': 'Structure'},
        color='oxygen_cylinders_available',
        color_continuous_scale='Blues'
    )
    # Flip the Y-axis to have the first one at the top
    fig_ops.update_layout(yaxis=dict(autorange="reversed"))
    
    st.plotly_chart(fig_ops, use_container_width=True)

    # --- FOOTER ---
    st.markdown("---")
    st.caption("Développé pour le test technique Sand Technologies - Forward Deployed Engineer - Babacar GUEYE.")