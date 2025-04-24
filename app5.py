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
import ast  # Para convertir strings de listas a listas reales
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg

# ---------- Configuración inicial de la página ----------
st.set_page_config(
    layout="wide",
    page_title="Customer Feedback Dashboard",
    page_icon="📊")

# ---------- Estilos CSS personalizados ----------
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .metric-title {
        font-size: 16px;
        color: #6c757d;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #343a40;
    }
    .metric-subtext {
        font-size: 14px;
        color: #6c757d;
        margin-top: 5px;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .full-width {
        width: 100%;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------- Carga de archivo ----------
with st.sidebar:
    st.image("logo.jpg", width=150)
    st.title("Filtros")
    archivo = st.file_uploader("Subir archivo Excel", type=["xlsx"])
    
    if archivo is not None:
        df = pd.read_excel(archivo)
        # Filtros principales
        ciudades = ['Todas'] + sorted(df['city'].dropna().unique().tolist())
        ciudad_seleccionada = st.selectbox("Seleccionar ciudad", ciudades)
        
        categorias = ['Todas'] + sorted(df['predicted_category'].dropna().unique().tolist())
        categoria_seleccionada = st.selectbox("Seleccionar categoría", categorias)
        
        sentimientos = ['Todos'] + sorted(df['Clasificacion'].dropna().unique().tolist())
        sentimiento_seleccionado = st.selectbox("Seleccionar sentimiento", sentimientos)

        productos = ['Todos'] + sorted(df['product type'].dropna().unique().tolist())
        productos_seleccionado = st.selectbox("Seleccionar el tipo de producto", productos)
        
# ---------- Contenido principal ----------
if archivo is not None:
    # Aplicar filtros
    if ciudad_seleccionada != 'Todas':
        df = df[df['city'] == ciudad_seleccionada]
    if categoria_seleccionada != 'Todas':
        df = df[df['predicted_category'] == categoria_seleccionada]
    if sentimiento_seleccionado != 'Todos':
        df = df[df['Clasificacion'] == sentimiento_seleccionado]
    if productos_seleccionado != 'Todos':
        df= df[df['product type']== productos_seleccionado]
    
    # ---------- Sección de métricas ----------
    st.title("📊 Customer Feedback Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-title">Total de Opiniones</div>
                <div class="metric-value">{}</div>
            </div>
            """.format(len(df)), unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-title">Ciudades Únicas</div>
                <div class="metric-value">{}</div>
                <div class="metric-subtext">Top: {}</div>
            </div>
            """.format(
                df['city'].nunique(),
                df['city'].value_counts().idxmax() if not df.empty else "N/A"
            ), unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-title">Quejas</div>
                <div class="metric-value">{}</div>
                <div class="metric-subtext">Top: {}</div>
            </div>
            """.format(
                len(df[df['Clasificacion'] == 'Negativo']) if 'Clasificacion' in df.columns else "N/A",
                df['predicted_category'].value_counts().idxmax() if not df.empty else "N/A"
            ), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-title">Rating Promedio</div>
                <div class="metric-value">{:.1f} ⭐</div>
                <div class="metric-subtext">De 5 estrellas</div>
            </div>
            """.format(df['PuntajeEstrellas'].mean() if 'PuntajeEstrellas' in df.columns else 0), unsafe_allow_html=True)
    
    # ---------- Mapa completo ----------
    st.markdown("---")
    st.subheader("Distribución Geográfica")
    
    if 'state_code' in df.columns:
        # Contar registros por estado
        state_counts = df['state_code'].value_counts().reset_index()
        state_counts.columns = ['state_code', 'count']
        state_data = dict(zip(state_counts['state_code'], state_counts['count']))
        
        # Obtener GeoJSON
        url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json'
        geo_json_data = requests.get(url).json()
        
        # Crear colormap
        custom_colors = ["#F2A30F", "#F22259"]
        min_count = min(state_data.values()) if state_data else 0
        max_count = max(state_data.values()) if state_data else 1
        colormap = LinearColormap(colors=custom_colors, vmin=min_count, vmax=max_count)
        
        # Crear mapa
        us_map = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
        folium.GeoJson(
            geo_json_data,
            name='choropleth',
            style_function=lambda feature: {
                'fillColor': colormap(state_data.get(feature['id'], 0)),
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.7,},
            tooltip=folium.GeoJsonTooltip(
                fields=['name'], 
                aliases=['Estado:'],
                localize=True)).add_to(us_map)
        
        colormap.caption = 'Cantidad de Registros por Estado'
        colormap.add_to(us_map)
        
        folium_static(us_map, width=1200, height=500)
    else:
        st.warning("No se encontró la columna 'state_code' para generar el mapa")
        
        # ---------- Gráfico de evolución temporal de quejas ----------
    st.markdown("---")
    st.subheader("Evolución Temporal de Quejas")

    if 'Email sent date' in df.columns and 'predicted_category' in df.columns:
        df['Email sent date'] = pd.to_datetime(df['Email sent date'], errors='coerce')
        df = df.dropna(subset=['Email sent date'])  # Quitar fechas inválidas

        fig = plt.figure(figsize=(16, 9))
        df.set_index('Email sent date')['predicted_category'].resample('W').count().plot()
        plt.suptitle("Evolución Temporal de Quejas", fontsize=20, fontweight='bold')
        plt.title("Tendencia semanal de recepción de quejas", fontsize=14)
        plt.xlabel("Fecha")
        plt.ylabel("Número de Quejas")
        plt.grid(True)
        plt.tight_layout()

        st.pyplot(fig)
    else:
        st.warning("No se encontró la columna 'Email sent date' o 'predicted_category'")
    
    # ---------- Tabla de resumen por categoría (ancho completo) ----------
    st.markdown("---")
    st.subheader("Resumen por Categoría")

    if not df.empty and 'predicted_category' in df.columns:
        resumen_categoria = df.groupby('predicted_category').agg({
            'PuntajeEstrellas': ['count', 'mean'],
            'confidence': 'mean' if 'confidence' in df.columns else None})

        # Renombrar columnas
        resumen_categoria.columns = ['Total', 'Rating Promedio', 'Confianza Promedio']

        # Aplicar formato y gradiente de color (evitando la columna "Total")
        styled = resumen_categoria.style \
            .format({'Confianza Promedio': '{:.1%}'}) \
            .background_gradient(cmap='YlOrRd_r', subset=['Rating Promedio', 'Confianza Promedio'])

        st.dataframe(styled, use_container_width=True)
    else:
        st.warning("No hay datos disponibles para mostrar el resumen por categoría")
    # ---------- Nueva tabla de detalles ----------
    st.markdown("---")
    st.subheader("Detalles de Quejas")
    
    # Verificar que las columnas solicitadas existan
    df[['Buyeridentity', 'AccountName_SalegRep', 'StreetAddress', 'PhoneNumber',
        'ContactName', 'Qty', 'ShipperKitPartNumber', 'Johnson_Johnson Site',
        'Return', 'No ChargePO']] = ''

    columnas_solicitadas = ['Buyeridentity', 'complaint id','subject', 'product type' ,'product code',
                            'AccountName_SalegRep','kits request', 'product for return','StreetAddress',
                            'city','state_name','zip code','PhoneNumber','hospital name', 'ContactName',
                            'Qty','ShipperKitPartNumber', 'JohnsonAnd.Johnson Site','Return', 
                            'No ChargePO','hospital ncp', 'email address']
    
    columnas_disponibles = [col for col in columnas_solicitadas if col in df.columns]
    
    if columnas_disponibles:
        st.dataframe(
            df[columnas_disponibles].dropna(how='all'),
            use_container_width=True
        )
    else:
        st.warning("No se encontraron las columnas solicitadas en el archivo")
    
    # ---------- Gráficos en pestañas (incluyendo nueva pestaña de Word Cloud) ----------
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Distribución", "⭐ Ratings", "😊 Sentimiento", "☁️ Nube de Palabras"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Opiniones por Categoría")
            if 'predicted_category' in df.columns:
                categoria_agrupada = df.groupby("predicted_category")["PuntajeEstrellas"].count()
                st.bar_chart(categoria_agrupada)
            else:
                st.warning("No se encontró la columna 'predicted_category'")
        
        with col2:
            st.subheader("Top 10 Ciudades")
            if 'city' in df.columns:
                top_ciudades = df['city'].value_counts().head(10)
                st.bar_chart(top_ciudades)
            else:
                st.warning("No se encontró la columna 'city'")
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Rating Promedio por Categoría")
            if 'predicted_category' in df.columns and 'PuntajeEstrellas' in df.columns:
                promedio_estrellas = df.groupby("predicted_category")["PuntajeEstrellas"].mean()
                st.bar_chart(promedio_estrellas)
            else:
                st.warning("Columnas necesarias no encontradas")
        
        with col2:
            st.subheader("Distribución de Ratings")
            if 'PuntajeEstrellas' in df.columns:
                rating_counts = df['PuntajeEstrellas'].value_counts().sort_index()
                st.bar_chart(rating_counts)
            else:
                st.warning("No se encontró la columna 'PuntajeEstrellas'")
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Distribución de Sentimientos")
            if 'Clasificacion' in df.columns:
                sentimiento = df["Clasificacion"].value_counts()
                st.bar_chart(sentimiento)
            else:
                st.warning("No se encontró la columna 'Clasificacion'")
        
        with col2:
            st.subheader("Sentimiento por Categoría")
            if 'predicted_category' in df.columns and 'Clasificacion' in df.columns:
                sentimiento_categoria = pd.crosstab(df['predicted_category'], df['Clasificacion'])
                st.bar_chart(sentimiento_categoria)
            else:
                st.warning("Columnas necesarias no encontradas")
    
    with tab4:
        st.subheader("Nube de Palabras de Comentarios")
        
        if 'tokens' in df.columns:
            try:
                # Convertir strings de listas a listas reales
                df['tokens'] = df['tokens'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
                
                # Concatenar todos los tokens
                all_tokens = [token for sublist in df['tokens'].dropna() for token in sublist]
                
                if all_tokens:
                    # Contar frecuencia de palabras
                    word_freq = Counter(all_tokens)
                    
                    # Filtrar palabras muy cortas
                    filtered_words = {word: count for word, count in word_freq.items() if len(word) > 2}
                    
                    # Leer stopwords desde el archivo
                    with open("stop_words_english.txt", "r") as file:
                        stop_words = set(file.read().splitlines())

                    # Filtrar las palabras que no están en las stopwords
                    filtered_words = {word: count for word, count in filtered_words.items() if word not in stop_words}
                    
                    # Generar wordcloud
                    wordcloud = WordCloud(width=800, height=400, 
                                        background_color='white',
                                        colormap='viridis').generate_from_frequencies(filtered_words)
                    
                    # Mostrar
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
    st.info("Por favor, sube un archivo Excel para comenzar el análisis")

# ---------- Sección para generar el reporte ----------
st.markdown("---")
st.subheader("📄 Generar Reporte PDF")

if st.button("Generar Reporte PDF"):
    pdf_path = "reporte_general_quejas.pdf"  # Guardar local
    logo_path = "logo.jpg"  # Asegúrate de tener este archivo en la misma carpeta
            
    def agregar_logo(fig):
        try:
            logo = mpimg.imread(logo_path)
            fig_width = fig.get_figwidth() * fig.dpi # Obtener dimensiones de la figura para posicionamiento relativo
            logo_width = logo.shape[1]  # Ancho del logo en píxeles
            
            # Posicionar el logo en el lado derecho con un margen de 10 píxeles
            fig.figimage(logo, xo=fig_width - logo_width - 10, yo=20, alpha=0.5, zorder=10, origin='upper')
        except Exception as e:
            print("No se pudo cargar el logo:", e)

    with PdfPages(pdf_path) as pdf:
        # ----------- PORTADA -----------
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.axis('off')
        fecha = datetime.today().strftime('%d %B %Y')
        ax.text(0.5, 0.7, 'Reporte General de Quejas', fontsize=32, fontweight='bold', ha='center')
        ax.text(0.5, 0.5, 'Análisis de Categorías, Sentimientos y Ciudades', fontsize=20, ha='center')
        ax.text(0.5, 0.3, f'Fecha del reporte: {fecha}', fontsize=16, ha='center', style='italic')
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
        
        categorias = ["• Request for shipping to the user's postal address",
                      "• Request for shipping to a specific hospital",
                      "• Accidentally lost inside the hospital",
                      "• Never received and still waiting",
                      "• Request for tracking confirmation shipment"]

        titulo = 'Resumen General de Datos'
        estadisticas = (f"Total de mensajes analizados: {num_mensajes}\n"
                        f"Cantidad de ciudades distintas: {num_ciudades}\n"
                        f"Cantidad de categorías predichas: {num_categorias}\n"
                        f"Promedio general de estrellas: {promedio_estrellas:.2f}\n\n"
                        "Categorías disponibles:\n" + "\n".join(categorias))

        ax.text(0.5, 0.95, titulo, fontsize=24, fontweight='bold', ha='center')
        ax.text(0.5, 0.6, estadisticas, fontsize=16, ha='center', va='top')

        agregar_logo(fig)
        pdf.savefig(fig)
        plt.close()
        
        # ----------- PERCEPCIÓN POR CATEGORÍA -----------
        fig = plt.figure(figsize=(16, 9))
        category_order = df.groupby("predicted_category")["PuntajeEstrellas"].mean().sort_values(ascending=False).index
        category_count = df.groupby("predicted_category")["PuntajeEstrellas"].count()
        bars = plt.bar(category_order, category_count.loc[category_order], color="skyblue")
        for bar, category in zip(bars, category_order):
            stars = df[df["predicted_category"] == category]["PuntajeEstrellas"].mean()
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                     f'{stars:.1f}', ha='center', va='bottom', fontsize=12)
        plt.suptitle("Percepción por Categoría", fontsize=20, fontweight='bold')
        plt.title("Distribución de Categorías Ordenadas por Estrellas Promedio", fontsize=14)
        plt.xlabel("Categoría", ha="left")
        plt.ylabel("Cantidad de Opiniones", va='bottom')
        plt.xticks(rotation=15, ha="left")
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()

        # ----------- DISTRIBUCIÓN DE SENTIMIENTOS -----------
        fig = plt.figure(figsize=(16, 9))
        clasificacion_ordenada = ["Positivo", "Neutro", "Negativo"]
        conteos = df["Clasificacion"].value_counts().reindex(clasificacion_ordenada)
        colores = ["green", "gray", "red"]
        bars = plt.bar(conteos.index, conteos.values, color=colores)
        for bar, count in zip(bars, conteos.values):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                     str(count), ha='center', va='bottom', fontsize=12)
        plt.suptitle("Distribución de Sentimientos", fontsize=20, fontweight='bold')
        plt.title("Sentimientos en los Mensajes Recibidos", fontsize=14)
        plt.xlabel("Clasificación")
        plt.ylabel("Cantidad de Mensajes")
        plt.tight_layout()
        plt.close()

        # ----------- CATEGORÍAS GENERALES PREDICHAS -----------
        fig = plt.figure(figsize=(16, 9))
        category_count = df["predicted_category"].value_counts()
        total = category_count.sum()
        bars = plt.bar(category_count.index, category_count.values,
                       color=['skyblue', 'salmon', 'lightgreen', 'lightcoral', 'gold'])
        for bar, count in zip(bars, category_count.values):
            percentage = (count / total) * 100
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                     f'{percentage:.1f}%', ha='center', va='bottom', fontsize=12)
        plt.suptitle("Categorías Generales Predichas", fontsize=20, fontweight='bold')
        plt.title("Distribución de Categorías de Correo Predichas", fontsize=14)
        plt.xlabel("Categoría Predicha")
        plt.ylabel("Número de Mensajes")
        plt.xticks(rotation=15, ha="left")
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()
        
      # ----------- DISTRIBUCIÓN DE QUEJAS POR ESTADO -----------            
        fig = plt.figure(figsize=(16, 9))
        state_counts = df['state_name'].value_counts().head()
        state_counts = state_counts.sort_values(ascending=True)
        state_counts.index = state_counts.index.astype(str)  # Asegura que sean strings

        bars = state_counts.plot(kind='barh', color='teal', alpha=0.7)

        plt.suptitle("Distribución de Quejas por Estado", fontsize=20, fontweight='bold')
        plt.title("Top 10 estados con más quejas (ordenados por frecuencia)", fontsize=14, pad=20)
        plt.xlabel("Número de Quejas", fontsize=12)
        plt.ylabel("Estado", fontsize=12)

        for i, (count, state) in enumerate(zip(state_counts, state_counts.index)):
            label = f"{count} ({count/len(df)*100:.1f}%)"
            plt.text(count + 0.5, i, label, va='center', fontsize=11, color='black')

        plt.tight_layout()
        plt.subplots_adjust(left=0.2)
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
        fig.suptitle("Categorías Predichas por Ciudad", fontsize=20, fontweight="bold")
        axes = axes.flatten()

        for i, city in enumerate(cities_to_plot):
            city_data = df[df["city"] == city]
            category_count = city_data["predicted_category"].value_counts()
            total = category_count.sum()
            bars = axes[i].bar(category_count.index, category_count.values,
                               color=['skyblue', 'salmon', 'lightgreen', 'lightcoral', 'gold'])
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
            fig.suptitle("Ciudades con una sola categoría predicha", fontsize=20, fontweight="bold")
            plt.subplots_adjust(left=0.1, right=0.9, top=0.98, bottom=0.1)
            agregar_logo(fig)
            pdf.savefig(fig)
            plt.close()
            
            # ----------- TOP 10 PRODUCTOS CON MÁS QUEJAS -----------
        fig = plt.figure(figsize=(16, 9))
        top_products = df['product type'].value_counts().head(10)
        top_products.plot(kind='barh', color='purple')
        plt.suptitle("Productos con Más Quejas", fontsize=20, fontweight='bold')
        plt.title("Top 10 tipos de productos mencionados en quejas", fontsize=14)
        plt.xlabel("Número de Quejas")
        plt.ylabel("Tipo de Producto")
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()
        
        # ----------- SERIE TEMPORAL DE QUEJAS -----------
        fig = plt.figure(figsize=(16, 9))
        df['Email sent date'] = pd.to_datetime(df['Email sent date'])
        df.set_index('Email sent date')['predicted_category'].resample('W').count().plot()
        plt.suptitle("Evolución Temporal de Quejas", fontsize=20, fontweight='bold')
        plt.title("Tendencia semanal de recepción de quejas", fontsize=14)
        plt.xlabel("Fecha")
        plt.ylabel("Número de Quejas")
        plt.grid(True)
        plt.tight_layout()
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

        ax.text(0.5, 0.95, 'Conclusiones y Hallazgos Clave', fontsize=24, fontweight='bold', ha='center', va='top')
        ax.text(0.5, 0.85, "Resumen ejecutivo de los principales insights", fontsize=14, ha='center', va='top', style='italic')

        # Usar textwrap para manejar mejor el formato
        lines = conclusiones.split('\n')
        y_position = 0.75
        for line in lines:
            if line.strip() == "":
                y_position -= 0.04  # Espacio adicional entre párrafos
            else:
                ax.text(0.1, y_position, line, 
                        fontsize=14, ha='left', va='top', wrap=True)
                y_position -= 0.06  # Espaciado entre líneas

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