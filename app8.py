from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import folium
import requests
from branca.colormap import LinearColormap
from streamlit_folium import folium_static
from wordcloud import WordCloud
from collections import Counter
import ast
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg
from matplotlib.colors import LinearSegmentedColormap
#hola

# ---------- Configuración inicial de la página ----------
st.set_page_config(
    layout="wide",
    page_title="Customer Feedback Dashboard",
    page_icon="📊")

colores_empresa = {
    'primary': '#F22259',
    'secondary': '#F23D91',
    'accent': '#6F04D9',
    'warning': '#F2A30F',
    'danger': '#F20505',
    'light': '#fff6f8',
    'dark': '#343a40',
    'gradient': 'linear-gradient(135deg, #F22259 0%, #6F04D9 100%)'}
# Convertir a lista para gráficos
colores_empresa_lista = [
    colores_empresa['primary'],
    colores_empresa['secondary'],
    colores_empresa['accent'],
    colores_empresa['warning'],
    colores_empresa['danger']
]
# ---------- Estilos CSS personalizados actualizados ----------
def apply_plot_style():
    plt.style.use('seaborn')
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.prop_cycle'] = plt.cycler(color=colores_empresa)
    plt.rcParams['axes.titleweight'] = 'bold'
    plt.rcParams['axes.titlecolor'] = '#F22259'
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    
# ---------- Estilos CSS con la paleta corporativa ----------
st.markdown(f"""
<style>
:root {{
    --primary: {colores_empresa['primary']};
    --secondary: {colores_empresa['secondary']};
    --accent: {colores_empresa['accent']};
    --warning: {colores_empresa['warning']};
    --danger: {colores_empresa['danger']};
    --light: {colores_empresa['light']};
    --dark: {colores_empresa['dark']};}}
/* ---------- Header Moderno ---------- */
.header {{
    background: {colores_empresa['gradient']};
    color: white;
    padding: 2rem 1rem;
    border-radius: 0 0 15px 15px;
    margin: -1rem -1rem 2rem -1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    text-align: center;}}

/* ---------- Tarjetas Métricas ---------- */
.metric-card {{
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
    height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border-left: 5px solid var(--primary);}}
    
/* ---------- Estilo para los tabs---------- */
        .stTabs [data-baseweb="tab"] {{
            font-size: 18px;
            padding: 16px 32px;
            min-width: 200px;
            flex-grow: 1;
            justify-content: center;
        }}

        /* Efecto hover para tarjetas métricas */
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(242, 34, 89, 0.15);
        }}

        /* Valor de la métrica con gradiente corporativo */
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            background: {colores_empresa['gradient']};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {{
    background: var(--light);
    border-right: 1px solid rgba(0,0,0,0.1);}}

/* ---------- Botones ---------- */
.stButton>button {{
    background: var(--primary);
    transition: all 0.3s ease;}}

.stButton>button:hover {{
    background: var(--secondary);
    transform: translateY(-2px);}}

/* ---------- Pestañas ---------- */
.stTabs [aria-selected="true"] {{
    background: var(--primary) !important;
    color: white !important;}}

/* ---------- Tablas ---------- */
.stDataFrame thead th {{
    background: var(--primary) !important;
    color: white !important;}}

/* ---------- Responsive ---------- */
@media (max-width: 768px) {{
    .metric-card {{
        height: auto;
        margin-bottom: 1rem;}}}}
</style>

<div class="header">
    <div class="header-title">📊 Customer Feedback Dashboard</div>
    <div class="header-subtitle">Análisis inteligente de quejas</div>
</div>
""", unsafe_allow_html=True)
# ---------- Carga de archivo ----------
with st.sidebar:
    st.image("logo.jpg", width=150)
    st.title("Filtros")
    archivo = st.file_uploader("Subir archivo Excel", type=["xlsx"])
    filtros = {}

    if archivo is not None:  # Solo intentar cargar el archivo si no es None
        try:
            df = pd.read_excel(archivo)
            st.session_state.df = df
            st.success("Archivo cargado correctamente")
            
            # Verificar si las columnas necesarias existen
            if 'city' not in df.columns or 'predicted_category' not in df.columns:
                st.warning("El archivo no contiene las columnas necesarias para el análisis.")
                df = pd.DataFrame()  # Reiniciar el DataFrame si no hay columnas necesarias
            
            # Filtros dinámicos con verificación de columnas
            columnas_disponibles = df.columns.tolist()
            
            if 'city' in columnas_disponibles:
                ciudades = ['Todas'] + sorted(df['city'].dropna().unique().tolist())
                filtros['city'] = st.selectbox("Seleccionar ciudad", ciudades)
            
            if 'predicted_category' in columnas_disponibles:
                categorias = ['Todas'] + sorted(df['predicted_category'].dropna().unique().tolist())
                filtros['predicted_category'] = st.selectbox("Seleccionar categoría", categorias)
            
            if 'Clasificacion' in columnas_disponibles:
                sentimientos = ['Todos'] + sorted(df['Clasificacion'].dropna().unique().tolist())
                filtros['Clasificacion'] = st.selectbox("Seleccionar sentimiento", sentimientos)

            if 'product type' in columnas_disponibles:
                productos = ['Todos'] + sorted(df['product type'].dropna().unique().tolist())
                filtros['product type'] = st.selectbox("Seleccionar producto", productos)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Por favor, sube un archivo Excel.")

# ---------- Procesamiento de datos ----------
if 'df' in locals() and not df.empty:
    # Aplicar filtros de forma segura
    for col, valor in filtros.items():
        if valor not in ['Todas', 'Todos']:
            df = df[df[col] == valor]
    
    # ---------- Botón para generar PDF (parte superior) ----------
st.markdown("---")
st.subheader("Reporte")

if st.button("📥 Generar Reporte PDF", use_container_width=True):
    if df.empty:
        st.warning("No hay datos para generar el reporte")
    else:
        try:
            pdf_path = "reporte_general_quejas.pdf"

            def agregar_logo(fig):
                try:
                    logo = mpimg.imread("logo.jpg")
                    fig_width = fig.get_figwidth() * fig.dpi
                    logo_width = logo.shape[1]
                    fig.figimage(logo, xo=fig_width - logo_width - 10, yo=20, alpha=0.5, zorder=10, origin='upper')
                except Exception as e:
                    st.error(f"Error al agregar el logo: {str(e)}")

            with PdfPages(pdf_path) as pdf:
                # ----------- PORTADA -----------
                fig, ax = plt.subplots(figsize=(16, 9))
                ax.axis('off')
                ax.set_facecolor(colores_empresa['primary'])
                fig.patch.set_facecolor(colores_empresa['secondary'])
                ax.text(0.5, 0.7, 'Reporte de Feedback', fontsize=32, ha='center', color='white')
                ax.text(0.5, 0.6, datetime.today().strftime('%d/%m/%Y'), fontsize=16, ha='center', color='white')
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                # ----------- DISTRIBUCIÓN POR CATEGORÍA -----------
                if 'predicted_category' in df.columns and 'PuntajeEstrellas' in df.columns:
                    fig, ax = plt.subplots(figsize=(16, 9))
                    category_counts = df['predicted_category'].value_counts()
                    category_counts.plot(kind='bar', color=colores_empresa_lista)
                    plt.title("Distribución por Categoría", fontsize=20, color=colores_empresa['primary'])
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    agregar_logo(fig)
                    pdf.savefig(fig)
                    plt.close()

                # ----------- RESUMEN GENERAL DE DATOS -----------
                fig, ax = plt.subplots(figsize=(16, 9))
                ax.axis('off')
                num_ciudades = df["city"].nunique()
                num_categorias = df["predicted_category"].nunique()
                num_mensajes = len(df)
                promedio_estrellas = df["PuntajeEstrellas"].mean()
                categorias = [
                    "• Request for shipping to the user's postal address",
                    "• Request for shipping to a specific hospital",
                    "• Accidentally lost inside the hospital",
                    "• Never received and still waiting",
                    "• Request for tracking confirmation shipment"
                ]
                estadisticas = (f"Total de mensajes analizados: {num_mensajes}\n"
                                f"Cantidad de ciudades distintas: {num_ciudades}\n"
                                f"Cantidad de categorías predichas: {num_categorias}\n"
                                f"Promedio general de estrellas: {promedio_estrellas:.2f}\n\n"
                                "Categorías disponibles:\n" + "\n".join(categorias))
                ax.text(0.5, 0.95, 'Resumen General de Datos', fontsize=24, fontweight='bold', ha='center', color=colores_empresa[0])
                ax.text(0.5, 0.6, estadisticas, fontsize=16, ha='center', va='top')
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()
                    
                    # ----------- PERCEPCIÓN POR CATEGORÍA -----------
                fig = plt.figure(figsize=(16, 9))
                category_order = df.groupby("predicted_category")["PuntajeEstrellas"].mean().sort_values(ascending=False).index
                category_count = df.groupby("predicted_category")["PuntajeEstrellas"].count()
                colors = colores_empresa * (len(category_order) // len(colores_empresa) + 1)
                bars = plt.bar(category_order, category_count.loc[category_order], color=colors[:len(category_order)])
                for bar, category in zip(bars, category_order):
                        stars = df[df["predicted_category"] == category]["PuntajeEstrellas"].mean()
                        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                                f'{stars:.1f}', ha='center', va='bottom', fontsize=12)
                plt.suptitle("Percepción por Categoría", fontsize=20, fontweight='bold', color=colores_empresa[0])
                plt.title("Distribución de Categorías Ordenadas por Estrellas Promedio", fontsize=14)
                plt.xlabel("Categoría", ha="left")
                plt.ylabel("Cantidad de Opiniones", va='bottom')
                plt.xticks(rotation=15, ha="left")
                plt.tight_layout()
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                    # ----------- DISTRIBUCIÓN DE SENTIMIENTOS -----------
                fig = plt.figure(figsize=(16, 9))
                clasificacion_ordenada = ["Positivo", "Neutro", "Negativo"]
                conteos = df["Clasificacion"].value_counts().reindex(clasificacion_ordenada)
                colores = [colores_empresa[3], colores_empresa[2], colores_empresa[0]]
                bars = plt.bar(conteos.index, conteos.values, color=colores)
                for bar, count in zip(bars, conteos.values):
                        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                                str(count), ha='center', va='bottom', fontsize=12)
                plt.suptitle("Distribución de Sentimientos", fontsize=20, fontweight='bold', color=colores_empresa[0])
                plt.title("Sentimientos en los Mensajes Recibidos", fontsize=14)
                plt.xlabel("Clasificación")
                plt.ylabel("Cantidad de Mensajes")
                plt.tight_layout()
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                    # ----------- CATEGORÍAS GENERALES PREDICHAS -----------
                fig = plt.figure(figsize=(16, 9))
                category_count = df["predicted_category"].value_counts()
                total = category_count.sum()
                colors = colores_empresa * (len(category_count) // len(colores_empresa) + 1)
                bars = plt.bar(category_count.index, category_count.values, color=colors[:len(category_count)])
                for bar, count in zip(bars, category_count.values):
                        percentage = (count / total) * 100
                        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                                f'{percentage:.1f}%', ha='center', va='bottom', fontsize=12)
                plt.suptitle("Categorías Generales Predichas", fontsize=20, fontweight='bold', color=colores_empresa[0])
                plt.title("Distribución de Categorías de Correo Predichas", fontsize=14)
                plt.xlabel("Categoría Predicha")
                plt.ylabel("Número de Mensajes")
                plt.xticks(rotation=15, ha="left")
                plt.tight_layout()
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()
                    
                    # ----------- DISTRIBUCIÓN DE QUEJAS POR ESTADO -----------            
                fig = plt.figure(figsize=(16, 9))
                state_counts = df['state_name'].value_counts().head()
                state_counts = state_counts.sort_values(ascending=True)
                state_counts.index = state_counts.index.astype(str)
                bars = state_counts.plot(kind='barh', color=colores_empresa[1], alpha=0.7)
                plt.suptitle("Distribución de Quejas por Estado", fontsize=20, fontweight='bold', color=colores_empresa[0])
                plt.title("Top 10 estados con más quejas (ordenados por frecuencia)", fontsize=14, pad=20)
                plt.xlabel("Número de Quejas", fontsize=12)
                plt.ylabel("Estado", fontsize=12)
                for i, (count, state) in enumerate(zip(state_counts, state_counts.index)):
                    label = f"{count} ({count/len(df)*100:.1f}%)"
                    plt.text(count + 0.5, i, label, va='center', fontsize=11, color='black')
                plt.tight_layout()
                plt.subplots_adjust(left=0.2)
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                    # ----------- CATEGORÍAS POR CIUDAD -----------
                fig, ax = plt.subplots(figsize=(16, 9))
                city_category_counts = df.groupby("city")["predicted_category"].nunique()
                cities_to_plot = city_category_counts[city_category_counts > 1].index
                ciudades_unica_categoria = df[df["city"].isin(city_category_counts[city_category_counts == 1].index)][["city", "predicted_category"]].drop_duplicates()

                num_cols = 2
                num_rows = int(np.ceil(len(cities_to_plot) / num_cols))
                fig, axes = plt.subplots(num_rows, num_cols, figsize=(16, 5 * num_rows))
                fig.suptitle("Categorías Predichas por Ciudad", fontsize=20, fontweight="bold", color=colores_empresa[0])
                axes = axes.flatten()

                for i, city in enumerate(cities_to_plot):
                    city_data = df[df["city"] == city]
                    category_count = city_data["predicted_category"].value_counts()
                    total = category_count.sum()
                    colors = colores_empresa * (len(category_count) // len(colores_empresa) + 1)
                    bars = axes[i].bar(category_count.index, category_count.values, color=colors[:len(category_count)])
                    for bar, count in zip(bars, category_count.values):
                        percentage = (count / total) * 100
                        axes[i].text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                                        f'{percentage:.1f}%', ha='center', va='bottom', fontsize=10)
                    axes[i].set_title(f"Distribución en {city}", fontsize=12)
                    axes[i].set_xlabel("Categoría")
                    axes[i].set_ylabel("Cantidad")
                    axes[i].tick_params(axis='x', rotation=15)

                for j in range(i + 1, len(axes)):
                    fig.delaxes(axes[j])

                plt.tight_layout(pad=3.0)
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                # ----------- TABLA DE CIUDADES CON UNA CATEGORÍA -----------
                if not ciudades_unica_categoria.empty:
                    fig, ax = plt.subplots(figsize=(16, 9))
                    ax.axis('tight')
                    ax.axis('off')
                    table = ax.table(cellText=ciudades_unica_categoria.values,
                                        colLabels=["Ciudad", "Categoría"],
                                        cellLoc="center", loc="center",
                                        cellColours=[["#f5f5f5"]*2]*len(ciudades_unica_categoria))
                    fig.suptitle("Ciudades con una sola categoría predicha", fontsize=20, fontweight="bold", color=colores_empresa[0])
                    plt.subplots_adjust(left=0.1, right=0.9, top=0.98, bottom=0.1)
                    agregar_logo(fig)
                    pdf.savefig(fig)
                    plt.close()
                    
                    # ----------- TOP 10 PRODUCTOS CON MÁS QUEJAS -----------
                fig = plt.figure(figsize=(16, 9))
                top_products = df['product type'].value_counts().head(10)
                top_products.plot(kind='barh', color=colores_empresa[4])
                plt.suptitle("Productos con Más Quejas", fontsize=20, fontweight='bold', color=colores_empresa[0])
                plt.title("Top 10 tipos de productos mencionados en quejas", fontsize=14)
                plt.xlabel("Número de Quejas")
                plt.ylabel("Tipo de Producto")
                plt.tight_layout()
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()
                
                # ----------- SERIE TEMPORAL DE QUEJAS -----------
                fig = plt.figure(figsize=(16, 9))
                df['Email sent date'] = pd.to_datetime(df['Email sent date'])
                df.set_index('Email sent date')['predicted_category'].resample('W').count().plot(color=colores_empresa[0])
                plt.suptitle("Evolución Temporal de Quejas", fontsize=20, fontweight='bold', color=colores_empresa[0])
                plt.title("Tendencia semanal de recepción de quejas", fontsize=14)
                plt.xlabel("Fecha")
                plt.ylabel("Número de Quejas")
                plt.grid(True)
                plt.tight_layout()
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                # ----------- CONCLUSIONES AUTOMÁTICAS -----------
                fig, ax = plt.subplots(figsize=(16, 9))
                ax.axis('off')

                top_cat = df["predicted_category"].value_counts().idxmax()
                worst_cat = df.groupby("predicted_category")["PuntajeEstrellas"].mean().idxmin()
                best_city = df.groupby("city")["PuntajeEstrellas"].mean().idxmax()
                worst_city = df.groupby("city")["PuntajeEstrellas"].mean().idxmin()
                top_state = df['state_name'].value_counts().idxmax()
                top_product = df['product type'].value_counts().idxmax()
                sentiment_dist = df["Clasificacion"].value_counts(normalize=True) * 100
                
                conclusiones = (
                    "Principales Hallazgos:\n\n"
                    f"1. Categoría más frecuente: {top_cat} ({df['predicted_category'].value_counts()[top_cat]} quejas)\n"
                    f"2. Categoría peor valorada: {worst_cat} ({df.groupby('predicted_category')['PuntajeEstrellas'].mean()[worst_cat]:.1f} estrellas)\n\n"
                    f"3. Ciudad destacada: {best_city} (mejor puntaje: {df.groupby('city')['PuntajeEstrellas'].mean()[best_city]:.1f} estrellas)\n"
                    f"4. Ciudad problemática: {worst_city} (peor puntaje: {df.groupby('city')['PuntajeEstrellas'].mean()[worst_city]:.1f} estrellas)\n\n"
                    f"5. Estado con más quejas: {top_state}\n"
                    f"6. Producto más mencionado: {top_product}\n\n"
                    "Distribución de sentimientos:\n"
                    f"- Positivo: {sentiment_dist.get('Positivo', 0):.1f}%\n"
                    f"- Neutro: {sentiment_dist.get('Neutro', 0):.1f}%\n"
                    f"- Negativo: {sentiment_dist.get('Negativo', 0):.1f}%")

                ax.text(0.5, 0.95, 'Conclusiones y Hallazgos Clave', fontsize=24, fontweight='bold', ha='center', va='top', color=colores_empresa[0])
                ax.text(0.5, 0.85, "Resumen ejecutivo de los principales insights", fontsize=14, ha='center', va='top', style='italic')

                lines = conclusiones.split('\n')
                y_position = 0.75
                for line in lines:
                    if line.strip() == "":
                        y_position -= 0.04
                    else:
                        ax.text(0.1, y_position, line, 
                                fontsize=14, ha='left', va='top', wrap=True)
                        y_position -= 0.06

                agregar_logo(fig)
                plt.subplots_adjust(top=0.85, bottom=0.1)
                pdf.savefig(fig)
                plt.close()
            
                # Descargar el PDF generado
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label="📥 Descargar PDF",
                    data=pdf_bytes,
                    file_name="reporte_general_quejas.pdf",
                    mime="application/pdf")
            
        except Exception as e:
            st.error(f"Ocurrió un error al generar el PDF: {str(e)}")

if 'df' in locals() and not df.empty:
    # ---------- Sección de métricas ----------
    st.markdown("---")
    st.subheader("Información general")
    col1, col2, col3, col4 = st.columns(4)
    metricas = {
        'Total Opiniones': len(df),
        'Ciudades Únicas': df['city'].nunique() if 'city' in df.columns else 'N/A',
        'Quejas': len(df[df['Clasificacion'] == 'Negativo']) if 'Clasificacion' in df.columns else 'N/A',
        'Rating Promedio': df['PuntajeEstrellas'].mean() if 'PuntajeEstrellas' in df.columns else 0
    }

    for i, (nombre, valor) in enumerate(metricas.items()):
        valor_formateado = f"{valor:.1f}" if isinstance(valor, (int, float)) else valor
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{nombre}</div>
                <div class="metric-value">{valor_formateado}</div>
            </div>
            """, unsafe_allow_html=True)

        # ---------- Mapa corregido ----------
    if 'state_code' in df.columns:
        try:
            state_counts = df['state_code'].value_counts().reset_index()
            state_counts.columns = ['state_code', 'count']
            state_data = dict(zip(state_counts['state_code'], state_counts['count']))
            
            # Usar colores de la paleta corporativa
            colormap = LinearColormap(
                colors=[colores_empresa['primary'], colores_empresa['secondary'], colores_empresa['accent']],
                vmin=min(state_data.values(), default=0),
                vmax=max(state_data.values(), default=1))
            
            us_map = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
            
            # Añadir capa geográfica
            folium.GeoJson(
                requests.get('https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json').json(),
                style_function=lambda feature: {
                    'fillColor': colormap(state_data.get(feature['id'], 0)),
                    'color': 'black',
                    'weight': 0.5,
                    'fillOpacity': 0.7,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['name'],
                    aliases=['Estado:'],
                    localize=True
                )
            ).add_to(us_map)
            
            colormap.caption = 'Cantidad de Registros por Estado'
            colormap.add_to(us_map)
            
            st.markdown("---")
            st.subheader("Distribución Geográfica")
            folium_static(us_map, width=1200, height=500)
            
        except Exception as e:
            st.error(f"Error al generar el mapa: {str(e)}")
    # ---------- Gráfico de evolución temporal de quejas ----------
    st.markdown("---")
    st.subheader("Evolución Temporal de Quejas")

    if 'Email sent date' in df.columns and 'predicted_category' in df.columns:
        df['Email sent date'] = pd.to_datetime(df['Email sent date'], errors='coerce')
        df = df.dropna(subset=['Email sent date'])  # Quitar fechas inválidas
        fig = plt.figure(figsize=(16, 9))
        ax= df.set_index('Email sent date')['predicted_category'].resample('W').count().plot(color=colores_empresa_lista[2],grid=False )
        ax.grid(False)
        plt.suptitle("Tendencia semanal de recepción de quejas", fontsize=14, fontweight='bold', color=colores_empresa["dark"], x=0.0, ha='left')
        plt.xlabel("Fecha",labelpad=15, loc='left')
        plt.ylabel("Número de Quejas", labelpad=15, loc='bottom')
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning("No se encontró la columna 'Email sent date' o 'predicted_category'")
    
    # ---------- Tabla de resumen por categoría con gradiente personalizado ----------
    st.markdown("---")
    st.subheader("Resumen por Categoría")

    if not df.empty and 'predicted_category' in df.columns:
        resumen_categoria = df.groupby('predicted_category').agg({
            'PuntajeEstrellas': ['count', 'mean'],
            'confidence': 'mean' if 'confidence' in df.columns else None})

        # Renombrar columnas
        resumen_categoria.columns = ['Total', 'Rating Promedio', 'Confianza Promedio']

        # Crear colormap personalizado
        custom_cmap = LinearSegmentedColormap.from_list("empresa", colores_empresa_lista)

        # Aplicar formato y gradiente de color
        styled = resumen_categoria.style \
            .format({'Confianza Promedio': '{:.1%}'}) \
            .background_gradient(cmap=custom_cmap, subset=['Rating Promedio', 'Confianza Promedio'])

        st.dataframe(styled, use_container_width=True)
    else:
        st.warning("No hay datos disponibles para mostrar el resumen por categoría")
    
    # ---------- Nueva tabla de detalles ----------
    st.markdown("---")
    st.subheader("Detalles de Quejas")
    
    # Verificar que las columnas solicitadas existan
    df[['Buyer ID', 'Account Name Sales Rep', 'Street Address', 'Phone','Contact', 'Qty', 
        'Shipper Kit PartNumber', 'J&J Site','Return', 'No ChargePO']] = ''

    columnas_solicitadas = ['Buyer ID', 'complaint id','subject', 'product type' ,'product code',
                            'Account Name Sales Rep','kits request', 'product for return','Street Address',
                            'city','state_name','zip code','Phone','hospital name', 'Contact',
                            'Qty','Shipper Kit PartNumber', 'J&J Site','Return', 
                            'No ChargePO','hospital ncp', 'email address']
    columnas_disponibles = [col for col in columnas_solicitadas if col in df.columns]
    
    if columnas_disponibles:
        st.dataframe(
            df[columnas_disponibles].dropna(how='all'),
            use_container_width=True
        )
    else:
        st.warning("No se encontraron las columnas solicitadas en el archivo")
    
    # ---------- Gráficos en pestañas  ----------
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Distribución", "⭐ Ratings", "😊 Sentimiento", "☁️ Nube de Palabras"])
    figsize_uniforme = (8, 6)

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Opiniones por Categoría")
            if 'predicted_category' in df.columns:
                categoria_agrupada = df.groupby("predicted_category")["PuntajeEstrellas"].count().sort_values()
                fig, ax = plt.subplots(figsize=figsize_uniforme)
                ax.barh(categoria_agrupada.index, categoria_agrupada.values, color=colores_empresa_lista[0])
                ax.grid(False)
                st.pyplot(fig)
            else:
                st.warning("No se encontró la columna 'predicted_category'")

        with col2:
            st.subheader("Top 10 Ciudades")
            if 'city' in df.columns:
                top_ciudades = df['city'].value_counts().head(10).sort_values()
                fig, ax = plt.subplots(figsize=figsize_uniforme)
                ax.barh(top_ciudades.index, top_ciudades.values, color=colores_empresa_lista[1])
                ax.grid(False)
                st.pyplot(fig)
            else:
                st.warning("No se encontró la columna 'city'")

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Rating Promedio por Categoría")
            if 'predicted_category' in df.columns and 'PuntajeEstrellas' in df.columns:
                promedio_estrellas = df.groupby("predicted_category")["PuntajeEstrellas"].mean().sort_values()
                fig, ax = plt.subplots(figsize=figsize_uniforme)
                ax.barh(promedio_estrellas.index, promedio_estrellas.values, color=colores_empresa_lista[2])
                ax.grid(False)
                st.pyplot(fig)
            else:
                st.warning("Columnas necesarias no encontradas")

        with col2:
            st.subheader("Distribución de Ratings")
            if 'PuntajeEstrellas' in df.columns:
                rating_counts = df['PuntajeEstrellas'].value_counts().sort_index()
                fig, ax = plt.subplots(figsize=figsize_uniforme)
                ax.barh(rating_counts.index.astype(str), rating_counts.values, color=colores_empresa_lista[3])
                ax.grid(False)
                st.pyplot(fig)
            else:
                st.warning("No se encontró la columna 'PuntajeEstrellas'")

    with tab3:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Distribución de Sentimientos")
            if 'Clasificacion' in df.columns:
                sentimiento = df["Clasificacion"].value_counts().sort_values()
                fig, ax = plt.subplots(figsize=figsize_uniforme)
                ax.barh(sentimiento.index, sentimiento.values, color=colores_empresa_lista[4])
                ax.grid(False)
                st.pyplot(fig)
            else:
                st.warning("No se encontró la columna 'Clasificacion'")

        with col2:
            st.subheader("Sentimiento por Categoría")
            if 'predicted_category' in df.columns and 'Clasificacion' in df.columns:
                sentimiento_categoria = pd.crosstab(df['predicted_category'], df['Clasificacion']).sort_index()
                fig, ax = plt.subplots(figsize=figsize_uniforme)
                sentimiento_categoria.plot(kind='barh', stacked=True, ax=ax, color=colores_empresa_lista[:len(sentimiento_categoria.columns)])
                ax.grid(False)
                st.pyplot(fig)
            else:
                st.warning("Columnas necesarias no encontradas")

    with tab4:
        st.subheader("Nube de Palabras de Comentarios")

        if 'tokens' in df.columns:
            try:
                df['tokens'] = df['tokens'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x) # Convertir strings de listas a listas reales
                all_tokens = [token for sublist in df['tokens'].dropna() for token in sublist] # Concatenar todos los tokens

                if all_tokens:                   
                    word_freq = Counter(all_tokens)# Contar frecuencia de palabras

                    filtered_words = {word: count for word, count in word_freq.items() if len(word) > 2}# Filtrar palabras muy cortas
                    
                    with open("stop_words_english.txt", "r") as file:# Leer stopwords desde el archivo
                        stop_words = set(file.read().splitlines())
                    
                    filtered_words = {word: count for word, count in filtered_words.items() if word not in stop_words}# Filtrar las palabras que no están en las stopwords
                   
                    custom_colormap = LinearSegmentedColormap.from_list("empresa", colores_empresa_lista) # Crear colormap personalizado
                    
                    wordcloud = WordCloud(width=800, height=400, # Generar wordcloud
                                        background_color='white',
                                        colormap=custom_colormap).generate_from_frequencies(filtered_words)

                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                else:
                    st.warning("No hay tokens disponibles para generar la nube de palabras")
            except Exception as e:
                st.error(f"Error al procesar los tokens: {str(e)}")
        else:
            st.warning("No se encontró la columna 'tokens'")

    # ---------- Sección de comentarios ----------
    st.markdown("---")
    st.subheader("📝 Comentarios Destacados")
    
    if 'message' in df.columns:
        comentarios_positivos = df[df['Clasificacion'] == 'Positivo']['message'].dropna().sample(3).tolist()
        comentarios_negativos = df[df['Clasificacion'] == 'Negativo']['message'].dropna().sample(3).tolist()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**😊 Comentarios Positivos**")
            for comentario in comentarios_positivos:
                st.markdown(f"""
                <div style="background-color: #e6f7e6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    {comentario}
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("**😠 Comentarios Negativos**")
            for comentario in comentarios_negativos:
                st.markdown(f"""
                <div style="background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    {comentario}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No se encontró la columna 'message' con los comentarios")
else:
    st.info("Por el momento no hay información suficiente para el análisis.")
