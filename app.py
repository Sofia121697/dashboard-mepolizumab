import pandas as pd
import plotly.express as px
import streamlit as st

# =========================
# Configuración general
# =========================
st.set_page_config(
    page_title="Dashboard Mepolizumab CDMX",
    page_icon="💊",
    layout="wide"
)

DATA_PATH = "mepolizumab_sellout_cdmx_500.csv"


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """Carga y prepara la base de datos."""
    df = pd.read_csv(path)

    # Convertir periodo a fecha para facilitar ordenamiento y filtros.
    df["Periodo_dt"] = pd.to_datetime(df["Periodo"] + "-01", errors="coerce")

    # Asegurar columnas numéricas.
    numeric_cols = [
        "Unidades_Sell_Out_Sinteticas",
        "Precio_Unitario_Sintetico_MXN",
        "Importe_Sell_Out_Sintetico_MXN",
        "Objetivo_Unidades",
        "Cumplimiento_vs_Objetivo_pct",
        "Variacion_MoM_pct",
        "Pacientes_Estimados",
        "Dias_Stock_Out",
        "Inventario_Cierre_Unidades",
        "Cobertura_Dias_Estimada",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def format_mxn(value: float) -> str:
    return f"${value:,.0f} MXN"


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


df = load_data(DATA_PATH)

# =========================
# Sidebar / filtros
# =========================
st.sidebar.title("Filtros")

periodos = sorted(df["Periodo"].dropna().unique())
sectores = sorted(df["Sector"].dropna().unique())
instituciones = sorted(df["Institucion"].dropna().unique())
kpis_auditoria = sorted(df["KPI_Auditoria"].dropna().unique())

periodo_sel = st.sidebar.multiselect(
    "Periodo",
    options=periodos,
    default=periodos
)

sector_sel = st.sidebar.multiselect(
    "Sector",
    options=sectores,
    default=sectores
)

institucion_sel = st.sidebar.multiselect(
    "Institución",
    options=instituciones,
    default=instituciones
)

kpi_sel = st.sidebar.multiselect(
    "KPI de auditoría",
    options=kpis_auditoria,
    default=kpis_auditoria
)

df_filtrado = df[
    (df["Periodo"].isin(periodo_sel)) &
    (df["Sector"].isin(sector_sel)) &
    (df["Institucion"].isin(institucion_sel)) &
    (df["KPI_Auditoria"].isin(kpi_sel))
].copy()

# =========================
# Encabezado
# =========================
st.title("Dashboard inteligente de sell-out de Mepolizumab en CDMX")

st.markdown(
    """
    Este dashboard analiza una base de datos sintética de sell-out de Mepolizumab en instituciones
    de salud de la Ciudad de México. Permite revisar desempeño por periodo, sector e institución,
    así como detectar riesgos de stock-out y oportunidades comerciales o de acceso.
    """
)

st.info(
    "Nota: la base utilizada es sintética, por lo que los resultados deben interpretarse como un ejercicio académico de analítica de datos."
)

# =========================
# KPIs principales
# =========================
total_unidades = df_filtrado["Unidades_Sell_Out_Sinteticas"].sum()
total_importe = df_filtrado["Importe_Sell_Out_Sintetico_MXN"].sum()
total_objetivo = df_filtrado["Objetivo_Unidades"].sum()
cumplimiento_global = (total_unidades / total_objetivo * 100) if total_objetivo > 0 else 0
pacientes_estimados = df_filtrado["Pacientes_Estimados"].sum()
dias_stockout = df_filtrado["Dias_Stock_Out"].sum()
cobertura_promedio = df_filtrado["Cobertura_Dias_Estimada"].mean()
registros_rojo = (df_filtrado["KPI_Auditoria"] == "Rojo").sum()
porcentaje_rojo = (registros_rojo / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0

st.subheader("Indicadores clave")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Unidades sell-out", f"{total_unidades:,.0f}")
col2.metric("Importe sell-out", format_mxn(total_importe))
col3.metric("Cumplimiento global", format_pct(cumplimiento_global))
col4.metric("Pacientes estimados", f"{pacientes_estimados:,.0f}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("Días stock-out", f"{dias_stockout:,.0f}")
col6.metric("Cobertura promedio", f"{cobertura_promedio:,.1f} días" if pd.notna(cobertura_promedio) else "N/A")
col7.metric("Registros en rojo", f"{registros_rojo:,.0f}")
col8.metric("% registros en rojo", format_pct(porcentaje_rojo))

# =========================
# Tabs principales
# =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Tendencias",
    "Instituciones",
    "Sectores",
    "Riesgos y auditoría",
    "Simulador"
])

with tab1:
    st.subheader("Evolución mensual")

    mensual = (
        df_filtrado
        .groupby(["Periodo", "Mes"], as_index=False)
        .agg(
            Unidades=("Unidades_Sell_Out_Sinteticas", "sum"),
            Importe=("Importe_Sell_Out_Sintetico_MXN", "sum"),
            Objetivo=("Objetivo_Unidades", "sum"),
            StockOut=("Dias_Stock_Out", "sum")
        )
    )
    mensual["Periodo_dt"] = pd.to_datetime(mensual["Periodo"] + "-01", errors="coerce")
    mensual = mensual.sort_values("Periodo_dt")
    mensual["Cumplimiento_pct"] = mensual["Unidades"] / mensual["Objetivo"] * 100

    fig_unidades = px.line(
        mensual,
        x="Periodo",
        y="Unidades",
        markers=True,
        title="Unidades sell-out por mes"
    )
    st.plotly_chart(fig_unidades, use_container_width=True)

    fig_importe = px.bar(
        mensual,
        x="Periodo",
        y="Importe",
        title="Importe sell-out por mes",
        text_auto=".2s"
    )
    st.plotly_chart(fig_importe, use_container_width=True)

    fig_cumplimiento = px.line(
        mensual,
        x="Periodo",
        y="Cumplimiento_pct",
        markers=True,
        title="Cumplimiento global vs objetivo por mes"
    )
    st.plotly_chart(fig_cumplimiento, use_container_width=True)

with tab2:
    st.subheader("Ranking por institución")

    inst = (
        df_filtrado
        .groupby("Institucion", as_index=False)
        .agg(
            Unidades=("Unidades_Sell_Out_Sinteticas", "sum"),
            Importe=("Importe_Sell_Out_Sintetico_MXN", "sum"),
            Objetivo=("Objetivo_Unidades", "sum"),
            StockOut=("Dias_Stock_Out", "sum"),
            Cobertura=("Cobertura_Dias_Estimada", "mean")
        )
    )
    inst["Cumplimiento_pct"] = inst["Unidades"] / inst["Objetivo"] * 100
    inst_top = inst.sort_values("Unidades", ascending=False).head(15)

    fig_inst = px.bar(
        inst_top,
        x="Unidades",
        y="Institucion",
        orientation="h",
        title="Top 15 instituciones por unidades sell-out",
        text="Unidades"
    )
    fig_inst.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_inst, use_container_width=True)

    fig_disp = px.scatter(
        inst,
        x="Cobertura",
        y="Cumplimiento_pct",
        size="Unidades",
        hover_name="Institucion",
        title="Relación entre cobertura estimada y cumplimiento por institución"
    )
    st.plotly_chart(fig_disp, use_container_width=True)

    st.dataframe(
        inst.sort_values("Unidades", ascending=False),
        use_container_width=True,
        hide_index=True
    )

with tab3:
    st.subheader("Análisis por sector")

    sector = (
        df_filtrado
        .groupby("Sector", as_index=False)
        .agg(
            Unidades=("Unidades_Sell_Out_Sinteticas", "sum"),
            Importe=("Importe_Sell_Out_Sintetico_MXN", "sum"),
            Objetivo=("Objetivo_Unidades", "sum"),
            StockOut=("Dias_Stock_Out", "sum"),
            Cobertura=("Cobertura_Dias_Estimada", "mean")
        )
    )
    sector["Cumplimiento_pct"] = sector["Unidades"] / sector["Objetivo"] * 100

    fig_sector = px.bar(
        sector.sort_values("Cumplimiento_pct", ascending=False),
        x="Sector",
        y="Cumplimiento_pct",
        title="Cumplimiento contra objetivo por sector",
        text_auto=".1f"
    )
    st.plotly_chart(fig_sector, use_container_width=True)

    fig_sector_units = px.pie(
        sector,
        names="Sector",
        values="Unidades",
        title="Participación de unidades sell-out por sector"
    )
    st.plotly_chart(fig_sector_units, use_container_width=True)

    st.dataframe(sector, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Riesgos, stock-out y KPI de auditoría")

    auditoria = (
        df_filtrado
        .groupby("KPI_Auditoria", as_index=False)
        .size()
        .rename(columns={"size": "Registros"})
    )

    fig_auditoria = px.bar(
        auditoria,
        x="KPI_Auditoria",
        y="Registros",
        title="Distribución de registros por KPI de auditoría",
        text="Registros"
    )
    st.plotly_chart(fig_auditoria, use_container_width=True)

    stockout_inst = (
        df_filtrado
        .groupby("Institucion", as_index=False)
        .agg(StockOut=("Dias_Stock_Out", "sum"))
        .sort_values("StockOut", ascending=False)
        .head(15)
    )

    fig_stockout = px.bar(
        stockout_inst,
        x="StockOut",
        y="Institucion",
        orientation="h",
        title="Top 15 instituciones con más días de stock-out",
        text="StockOut"
    )
    fig_stockout.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_stockout, use_container_width=True)

    heat = (
        df_filtrado
        .groupby(["Institucion", "Periodo"], as_index=False)
        .agg(Cumplimiento=("Cumplimiento_vs_Objetivo_pct", "mean"))
    )

    top_heat_insts = (
        df_filtrado
        .groupby("Institucion")["Unidades_Sell_Out_Sinteticas"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
        .index
    )

    heat = heat[heat["Institucion"].isin(top_heat_insts)]

    fig_heat = px.density_heatmap(
        heat,
        x="Periodo",
        y="Institucion",
        z="Cumplimiento",
        histfunc="avg",
        title="Mapa de calor de cumplimiento por institución y periodo"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with tab5:
    st.subheader("Simulador de escenarios por reducción de stock-out")

    st.markdown(
        """
        Este módulo estima el impacto potencial de reducir días de stock-out.
        La simulación usa una lógica simple: calcula la demanda diaria aproximada y estima
        cuántas unidades e importe podrían recuperarse al disminuir los días sin disponibilidad.
        """
    )

    reduccion_pct = st.slider(
        "Reducción estimada de días de stock-out (%)",
        min_value=0,
        max_value=100,
        value=30,
        step=5
    )

    dias_periodo = st.number_input(
        "Días considerados por periodo",
        min_value=1,
        max_value=31,
        value=30,
        step=1
    )

    precio_promedio = df_filtrado["Precio_Unitario_Sintetico_MXN"].mean()

    df_sim = df_filtrado.copy()
    df_sim["Demanda_Diaria_Estimada"] = df_sim["Unidades_Sell_Out_Sinteticas"] / dias_periodo
    df_sim["Dias_StockOut_Reducidos"] = df_sim["Dias_Stock_Out"] * (reduccion_pct / 100)
    df_sim["Unidades_Recuperables"] = df_sim["Demanda_Diaria_Estimada"] * df_sim["Dias_StockOut_Reducidos"]
    df_sim["Importe_Recuperable"] = df_sim["Unidades_Recuperables"] * df_sim["Precio_Unitario_Sintetico_MXN"]

    unidades_recuperables = df_sim["Unidades_Recuperables"].sum()
    importe_recuperable = df_sim["Importe_Recuperable"].sum()

    sim_col1, sim_col2, sim_col3 = st.columns(3)
    sim_col1.metric("Unidades potencialmente recuperables", f"{unidades_recuperables:,.1f}")
    sim_col2.metric("Importe potencial recuperable", format_mxn(importe_recuperable))
    sim_col3.metric("Precio promedio utilizado", format_mxn(precio_promedio))

    sim_inst = (
        df_sim
        .groupby("Institucion", as_index=False)
        .agg(
            Unidades_Recuperables=("Unidades_Recuperables", "sum"),
            Importe_Recuperable=("Importe_Recuperable", "sum")
        )
        .sort_values("Importe_Recuperable", ascending=False)
        .head(15)
    )

    fig_sim = px.bar(
        sim_inst,
        x="Importe_Recuperable",
        y="Institucion",
        orientation="h",
        title="Top 15 instituciones por importe potencial recuperable",
        text_auto=".2s"
    )
    fig_sim.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_sim, use_container_width=True)

    st.dataframe(
        sim_inst,
        use_container_width=True,
        hide_index=True
    )

# =========================
# Hallazgos automáticos
# =========================
st.subheader("Hallazgos clave preliminares")

if len(df_filtrado) == 0:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    top_institucion = (
        df_filtrado
        .groupby("Institucion")["Unidades_Sell_Out_Sinteticas"]
        .sum()
        .sort_values(ascending=False)
    )

    top_sector = (
        df_filtrado
        .groupby("Sector")["Unidades_Sell_Out_Sinteticas"]
        .sum()
        .sort_values(ascending=False)
    )

    mayor_stockout = (
        df_filtrado
        .groupby("Institucion")["Dias_Stock_Out"]
        .sum()
        .sort_values(ascending=False)
    )

    st.markdown(
        f"""
        - La institución con mayor volumen de unidades sell-out es **{top_institucion.index[0]}** con **{top_institucion.iloc[0]:,.0f} unidades**.
        - El sector con mayor volumen de sell-out es **{top_sector.index[0]}** con **{top_sector.iloc[0]:,.0f} unidades**.
        - La institución con mayor acumulado de días de stock-out es **{mayor_stockout.index[0]}** con **{mayor_stockout.iloc[0]:,.0f} días**.
        - El cumplimiento global filtrado es de **{cumplimiento_global:.1f}%**.
        - El porcentaje de registros en rojo dentro de la selección actual es de **{porcentaje_rojo:.1f}%**.
        """
    )
