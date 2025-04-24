import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import folium
import requests
from branca.colormap import LinearColormap
from streamlit_folium import folium_static
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import matplotlib.image as mpimg
import base64
import io

# ---------- Configuración inicial de la página ----------
st.set_page_config(layout="wide")
st.title("Análisis de Opiniones de Usuarios")

# ---------- Carga de archivo ----------
archivo = st.file_uploader("Sube el archivo Excel con los datos de opiniones", type=["xlsx"])
logo_path = "logo.jpg"  # Debes subir también este archivo

if archivo is not None:
    df = pd.read_excel(archivo)

    # Verificación rápida de columnas necesarias
    columnas_necesarias = ["city", "predicted_category", "PuntajeEstrellas", "Clasificacion", "message"]
    if all(col in df.columns for col in columnas_necesarias):

        # ---------- Vista previa de datos ----------
        st.subheader("Vista previa de datos")
        st.dataframe(df.head())

        # ---------- Visualizaciones Streamlit ----------
        st.subheader("Distribución de Opiniones por Categoría")
        categoria_agrupada = df.groupby("predicted_category")["PuntajeEstrellas"].count()
        st.bar_chart(categoria_agrupada)

        st.subheader("Promedio de Estrellas por Categoría")
        promedio_estrellas = df.groupby("predicted_category")["PuntajeEstrellas"].mean()
        st.bar_chart(promedio_estrellas)

        st.subheader("Distribución de Sentimientos")
        sentimiento = df["Clasificacion"].value_counts()
        st.bar_chart(sentimiento)

        # ---------- Mapa Interactivo ----------
        st.subheader("Mapa Interactivo de Opiniones por Estado")

        # Contar registros por estado
        state_counts = df['state_code'].value_counts().reset_index()
        state_counts.columns = ['state_code', 'count']

        # Crear diccionario de valores para acceso rápido
        state_data = dict(zip(state_counts['state_code'], state_counts['count']))

        # Obtener el GeoJSON de los estados de EE.UU.
        url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json'
        geo_json_data = requests.get(url).json()

        # Crear colormap personalizado
        custom_colors = ["#F2A30F", "#F22259"]
        min_count = min(state_data.values())
        max_count = max(state_data.values())
        colormap = LinearColormap(colors=custom_colors, vmin=min_count, vmax=max_count)

        # Crear el mapa base
        us_map = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

        folium.GeoJson(
            geo_json_data,
            name='choropleth',
            style_function=lambda feature: {
                'fillColor': colormap(state_data.get(feature['id'], 0)),
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.7,
            },
            tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['Estado:'])
        ).add_to(us_map)

        colormap.caption = 'Cantidad de Registros por Estado'
        colormap.add_to(us_map)

        folium_static(us_map)

        # ---------- Botón para generar PDF ----------
        if st.button("📄 Generar Reporte PDF"):
            pdf_path = "/tmp/reporte_general_quejas.pdf"

            def agregar_logo(fig):
                try:
                    logo = mpimg.imread(logo_path)
                    fig.figimage(logo, xo=50, yo=20, alpha=0.5, zorder=10, origin='upper')
                except Exception as e:
                    print("No se pudo cargar el logo:", e)

            with PdfPages(pdf_path) as pdf:
                # DISTRIBUCIÓN POR CATEGORÍA
                fig, ax = plt.subplots(figsize=(10, 6))
                categoria_agrupada.plot(kind="bar", ax=ax)
                ax.set_title("Distribución de Opiniones por Categoría")
                ax.set_ylabel("Cantidad")
                plt.xticks(rotation=45)
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                # PROMEDIO DE ESTRELLAS
                fig, ax = plt.subplots(figsize=(10, 6))
                promedio_estrellas.plot(kind="bar", ax=ax, color='skyblue')
                ax.set_title("Promedio de Estrellas por Categoría")
                ax.set_ylabel("Promedio de Estrellas")
                plt.xticks(rotation=45)
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                # DISTRIBUCIÓN DE SENTIMIENTOS
                fig, ax = plt.subplots(figsize=(8, 6))
                sentimiento.plot(kind="bar", ax=ax, color='orange')
                ax.set_title("Distribución de Sentimientos")
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                # CONCLUSIONES
                fig, ax = plt.subplots(figsize=(16, 9))
                ax.axis('off')
                top_cat = df["predicted_category"].value_counts().idxmax()
                worst_cat = df.groupby("predicted_category")["PuntajeEstrellas"].mean().idxmin()
                best_city = df.groupby("city")["PuntajeEstrellas"].mean().idxmax()
                worst_city = df.groupby("city")["PuntajeEstrellas"].mean().idxmin()
                conclusiones = (
                    f"- La categoría con más quejas es: **{top_cat}**.\n"
                    f"- La categoría peor valorada es: **{worst_cat}**.\n"
                    f"- Ciudad con mejor percepción: **{best_city}**.\n"
                    f"- Ciudad con peor percepción: **{worst_city}**.\n"
                )
                ax.text(0.5, 0.8, 'Conclusiones', fontsize=24, fontweight='bold', ha='center')
                ax.text(0.5, 0.5, conclusiones, fontsize=16, ha='center', va='center', wrap=True)
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                # RECOMENDACIONES
                fig, ax = plt.subplots(figsize=(16, 9))
                ax.axis('off')
                recomendaciones = (
                    "- Priorizar la atención a la categoría con más quejas.\n"
                    "- Implementar mejoras en la categoría peor valorada.\n"
                    "- Reforzar buenas prácticas en las ciudades con mejor percepción.\n"
                    "- Analizar causas comunes en las ciudades con menor percepción para tomar acciones correctivas."
                )
                ax.text(0.5, 0.8, 'Recomendaciones', fontsize=24, fontweight='bold', ha='center')
                ax.text(0.5, 0.5, recomendaciones, fontsize=16, ha='center', va='center', wrap=True)
                agregar_logo(fig)
                pdf.savefig(fig)
                plt.close()

                # COMENTARIOS DESTACADOS POR SENTIMIENTO
                for clasificacion in ["Positivo", "Neutro", "Negativo"]:
                    fig, ax = plt.subplots(figsize=(16, 9))
                    ax.axis('off')
                    comentarios = df[df["Clasificacion"] == clasificacion]["message"].dropna().unique().tolist()
                    ejemplos = comentarios[:5] if len(comentarios) >= 5 else comentarios
                    texto = "\n\n".join([f"- {comentario}" for comentario in ejemplos])
                    ax.text(0.5, 0.9, f"Ejemplos de Comentarios {clasificacion}s", fontsize=24, fontweight='bold', ha='center')
                    ax.text(0.5, 0.45, texto, fontsize=12, ha='center', va='center', wrap=True)
                    agregar_logo(fig)
                    pdf.savefig(fig)
                    plt.close()

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button("📥 Descargar PDF generado", data=pdf_bytes, file_name="reporte_general_quejas.pdf", mime="application/pdf")
    else:
        st.warning("El archivo no contiene las columnas necesarias: 'city', 'predicted_category', 'PuntajeEstrellas', 'Clasificacion', 'message'")