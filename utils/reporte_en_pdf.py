# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.binary import Binary
from datetime import datetime
import numpy as np
import pandas as pd

from itertools import product
from fpdf import FPDF
from IPython.display import FileLink

from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler, PolynomialFeatures, StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    make_scorer,
    silhouette_score,
    silhouette_samples,
)
from sklearn.utils import resample
from utils.conexion_mongo import db
from io import BytesIO

def reporte_en_pdf(ventas):
    # Leer colecciones
    venta_df = pd.DataFrame(ventas)
    arriendo_df = pd.DataFrame(list(db["arriendo"].find()))

    # Quitar columna _id si no es necesaria
    venta_df.drop(columns="_id", inplace=True, errors="ignore")
    arriendo_df.drop(columns="_id", inplace=True, errors="ignore")


    def eliminar_columnas_inutiles(df,columnas_a_eliminar):

        df = df.drop(columns=columnas_a_eliminar, errors='ignore')
        print(f"✅ Columnas eliminadas: {columnas_a_eliminar}")
        return df

    def procesar_ubicacion_y_ciudad(df):
        # Diccionarios de agrupación
        regiones = {
            'Sabana de Bogotá': {'Chía', 'Chia', 'Madrid', 'Cajicá', 'Cajica', 'Sopo', 'Sopó', 'Mosquera', 'Cota', 'Subachoque', 'La calera', 'La Calera', 'Cundinamarca', 'Tocancipá', 'Zipaquirá'},
            'Área Metropolitana Medellín': {'Itagüí', 'Itagui', 'Itaguí', 'Bello', 'Rionegro', 'Antioquia'},
            'Eje Cafetero': {'Pereira', 'Dosquebradas', 'Santa Rosa de Cabal', 'Armenia', 'Calarcá', 'Villamaria', 'Quindio', 'Manizales'},
            'Norte de Santander': {'Cúcuta', 'Los patios', 'Villa del rosario'},
            'Área Metropolitana Bucaramanga': {'Bucaramanga', 'Floridablanca'},
            'Área Metropolitana Barranquilla': {'Barranquilla', 'Puerto Colombia', 'Atlántico'},
            'Cali': {'Jamundí', 'Palmira'}
        }

        def agrupar_ciudad(x):
            for nombre, grupo in regiones.items():
                if x in grupo:
                    return nombre
            return x

        df['Ciudad'] = df['Ciudad'].apply(agrupar_ciudad)

        conteo_ciudades = df['Ciudad'].value_counts()
        ciudades_comunes = conteo_ciudades[conteo_ciudades > 20].index
        df['Ciudad'] = df['Ciudad'].apply(lambda x: x if x in ciudades_comunes else 'Otro')

        print(f"🏙️ Columna 'Ciudad' agrupada. Total de ciudades finales: {df['Ciudad'].nunique()}")
        return df

    def limpiar_variables_numericas(df):
        # Área Construida
        df['Área Construida'] = (
            df['Área Construida']
            .astype(str)
            .str.split('.').str[0]
            .str.replace(',', '', regex=False)
            .str.strip()
        )
        df['Área Construida'] = pd.to_numeric(df['Área Construida'], errors='coerce')

        # Precio
        df['Precio'] = (
            df['Precio']
            .astype(str)
            .str.replace('$', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.strip()
        )
        df['Precio'] = pd.to_numeric(df['Precio'], errors='coerce')
        print("💰 Columna 'Precio' limpiada y convertida a numérico.")

        # Antigüedad
        mapa_antiguedad = {
            'menor a 1 año': 1, '1 a 8 años': 4, '9 a 15 años': 9,
            '16 a 30 años': 16, 'más de 30 años': 30, 'N/A': 9
        }
        df['Antiguedad_num'] = df['Antigüedad'].map(mapa_antiguedad)
        print("⏳ 'Antigüedad' convertida a 'Antiguedad_num'.")

        df.drop(columns=['Antigüedad'], inplace=True, errors='ignore')
        return df

    def convertir_columnas_a_numerico(df):
        for col in ['Baños', 'Habitaciones', 'Estrato']:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(',', '', regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df[['Baños', 'Habitaciones']] = df[['Baños', 'Habitaciones']].fillna(0)
        estrato_mean = df['Estrato'].mean()
        df['Estrato'] = df['Estrato'].fillna(estrato_mean)
        print("🧹 'Baños', 'Habitaciones' y 'Estrato' convertidos y NaN imputados.")
        return df

    def crear_dummies(df):
        columnas_dummies = ['Tipo de Inmueble', 'Ciudad']
        dummies = pd.get_dummies(df[columnas_dummies], drop_first=True)
        df = pd.concat([df.drop(columns=columnas_dummies), dummies], axis=1)

        df = df.astype({col: 'int' for col in df.select_dtypes(include='bool').columns})
        print(f"🏗️ Dummies creados para: {columnas_dummies}")
        return df


    '''def agregar_variables_contexto_ubicacion(df):
        """
        Agrega columnas que capturan información contextual de ubicación:
        - Precio_m2_ubicacion: promedio del precio por m² en cada ubicación
        - Precio_ubicacion: promedio del precio total en cada ubicación

        Requiere columnas: 'Precio', 'Área Construida', 'Ubicación'
        """
        df = df.copy()

        # Calcular precio por m² con protección por división por cero
        df['Precio_m2'] = df['Precio'] / (df['Área Construida'] + 1)

        # Agregar promedios por ubicación
        df['Precio_m2_ubicacion'] = df.groupby('Ubicación')['Precio_m2'].transform('mean')
        df['Precio_ubicacion'] = df.groupby('Ubicación')['Precio'].transform('mean')

        print("📍 Columnas 'Precio_m2_ubicacion' y 'Precio_ubicacion' creadas.")
        return df'''


    def agregar_variables_contexto_ubicacion(df):
        """
        Agrega columnas que capturan información contextual de ubicación:
        - Precio_m2_ubicacion: promedio del precio por m² en cada ubicación (leave-one-out)
        - Precio_ubicacion: promedio del precio total en cada ubicación (leave-one-out)

        Elimina ubicaciones con solo un registro (no se puede calcular LOO).
        Requiere columnas: 'Precio', 'Área Construida', 'Ubicación'
        """
        df = df.copy()

        # Calcular Precio por m² con protección por división por cero
        df['Precio_m2'] = df['Precio'] / (df['Área Construida'] + 1)

        # Contar cuántos datos tiene cada ubicación
        conteo_ubicaciones = df['Barrio'].value_counts()

        # Filtrar ubicaciones con más de 1 dato
        ubicaciones_validas = conteo_ubicaciones[conteo_ubicaciones > 1].index
        df = df[df['Barrio'].isin(ubicaciones_validas)].copy()

        # Leave-One-Out promedio
        def leave_one_out_mean(series):
            #return (series.sum() - series) / (series.count() - 1)
            return (series.sum()) / (series.count())
        df['Precio_ubicacion'] = df.groupby('Barrio')['Precio'].transform(leave_one_out_mean)
        df['Precio_m2_ubicacion'] = df.groupby('Barrio')['Precio_m2'].transform(leave_one_out_mean)

        print(f"📍 Columnas 'Precio_ubicacion' y 'Precio_m2_ubicacion' creadas con leave-one-out.")
        print(f"✅ Ubicaciones eliminadas por falta de datos: {conteo_ubicaciones[conteo_ubicaciones == 1].shape[0]}")

        return df
    def remover_outliers_area_precio(df, col_area='Área Construida', col_precio='Precio', area_max=None, precio_max=None):
        """
        Elimina filas con valores extremos en área y precio.

        Parámetros:
        - df: DataFrame original
        - col_area: nombre de la columna de área construida
        - col_precio: nombre de la columna de precio
        - area_max: umbral máximo de área (si None, se usa el percentil 99)
        - precio_max: umbral máximo de precio (si None, se usa el percentil 99)

        Retorna:
        - DataFrame limpio
        """
        df = df.copy()

        # Determinar umbrales automáticos si no se especifican
        if area_max is None:
            area_max = df[col_area].quantile(0.95)
        if precio_max is None:
            precio_max = df[col_precio].quantile(0.95)

        original_len = len(df)
        df = df[(df[col_area] <= area_max) & (df[col_precio] <= precio_max)]
        final_len = len(df)

        print(f"🧹 Se eliminaron {original_len - final_len} outliers. Área ≤ {area_max:.2f}, Precio ≤ {precio_max:,.0f}")

        return df
    def preprocesor_arriendo(df):
        """
        Función principal de preprocesamiento para datos de arriendo.
        Ejecuta los siguientes pasos:
        - Elimina columnas irrelevantes
        - Extrae y agrupa ciudad
        - Limpia y convierte variables numéricas
        - Imputa valores faltantes
        - Crea variables dummies
        - Escala variables numéricas
        Retorna:
        - df: DataFrame completo preprocesado
        - X: variables predictoras escaladas
        - y: variable objetivo (Precio)
        - X_sin_estandarizar: variables predictoras sin escalar
        """
        df = df.copy()
        columnas_a_eliminar = ['Enlace', 'Administración', 'Estado', 'Área Privada','Tipo de Inmueble','Tipo']
        df = eliminar_columnas_inutiles(df,columnas_a_eliminar)
        print(df.info)
        df = procesar_ubicacion_y_ciudad(df)
        df = limpiar_variables_numericas(df)
        print(df.info)
        df = convertir_columnas_a_numerico(df)

        print(df.info)
        #df = crear_dummies(df)
        df = agregar_variables_contexto_ubicacion(df)
        # Crear subconjunto sin estandarizar
        X_sin_estandarizar = df.drop(columns=['Precio'])

        # Separar variable objetivo
        y = df['Precio']
        X = df.drop(columns=['Precio'])
        df = remover_outliers_area_precio(df)
        # Variables numéricas a escalar
        columnas_a_estandarizar = ['Baños', 'Área Construida', 'Habitaciones', 'Antiguedad_num', 'Estrato']


        print(f"🎯 Preprocesamiento completado. X shape: {X.shape}, y shape: {y.shape}")
        return df, X, y, X_sin_estandarizar
    def limpiar_administracion(df):
        """
        Limpia la columna 'Administración' dejando solo el número:
        - Convierte 'N/A' en 0
        - Extrae números y elimina puntos o símbolos
        - Convierte el resultado a tipo numérico
        """
        df = df.copy()
        df['Administración'] = df['Administración'].astype(str)

        df['Administración'] = (
            df['Administración']
            .str.replace('.', '', regex=False)
            .str.extract(r'(\d+)')[0]  # Extrae solo los números iniciales
            .fillna('0')               # Llena con 0 si no se encuentra número
            .astype(int)               # Convierte a entero
        )

        print("🏢 Columna 'Administración' limpiada.")
        return df

    def preprocesor_venta(df,arriendo_data_ubicacion,kmeans):
        columnas_a_eliminar = ['Estado', 'Área Privada','Tipo de Inmueble','Tipo']
        df = eliminar_columnas_inutiles(df,columnas_a_eliminar)
        df = limpiar_variables_numericas(df)
        df = convertir_columnas_a_numerico(df)
        df = limpiar_administracion(df)
        df = df.merge(arriendo_data_ubicacion, on='Barrio', how='left')
        # 1. Variables usadas en el clustering
        features_cluster = ['Estrato', 'Baños', 'Área Construida', 'Habitaciones', 'Antiguedad_num',
                            'Precio_ubicacion', 'Precio_m2_ubicacion']

        # 2. Preprocesar las nuevas propiedades
        X_nuevas = df[features_cluster].dropna()  # Filtrar si hay NaNs
        X_nuevas_scaled = X_nuevas.copy()

        # 3. Aplicar el mismo escalado que se usó en clustering original

        # 4. Asignar clúster usando el modelo ya entrenado
        df.loc[X_nuevas.index, 'Cluster'] = kmeans.predict(X_nuevas_scaled)

        return df
    def calcular_roi_anual(ventas_df):
        """
        Calcula el porcentaje de retorno de inversión anual:
        ROI_anual_% = [(12 * (prediccion_precio - Administración)) / Precio] * 100
        Asume que 'prediccion_precio', 'Administración' y 'Precio' están en pesos colombianos.
        """
        df = ventas_df.copy()
        df['ROI_anual_%'] = (
            12 * (df['Prediccion_Precio'] - df['Administración']) / df['Precio']
        ) * 100

        print("📈 Columna 'ROI_anual_%' creada.")
        return df

    arriendo_df, X_arriendo, y_arriendo, X_arriendo_sin_estandarizar = preprocesor_arriendo(arriendo_df)

    # Seleccionar las columnas numéricas relevantes
    columnas_numericas = [
        'Estrato', 'Baños', 'Área Construida', 'Habitaciones',
        'Antiguedad_num', 'Precio_ubicacion', 'Precio_m2_ubicacion'
    ]

    # Eliminar filas con valores faltantes
    df_cluster = arriendo_df[columnas_numericas].dropna()

    # Escalar los datos
    X_scaled = df_cluster.copy()



    # Aplicar KMeans con 3 clústeres
    kmeans = KMeans(n_clusters=3, random_state=42)
    cluster_labels = kmeans.fit_predict(X_scaled)

    # Agregar etiquetas de clúster al DataFrame original
    arriendo_df['Cluster'] = cluster_labels



    # Definir las variables predictoras numéricas
    features = ['Estrato', 'Baños', 'Área Construida', 'Habitaciones', 'Antiguedad_num','Precio_ubicacion','Precio_m2_ubicacion']

    # Almacenar resultados por clúster
    resultados = []

    # Iterar por cada clúster
    for cluster_id in sorted(arriendo_df['Cluster'].unique()):
        df_cluster = arriendo_df[arriendo_df['Cluster'] == cluster_id]

        X = df_cluster[features]
        y = df_cluster['Precio']

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        y_pred = model.predict(X)

        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        relative_error = np.mean(np.abs(y - y_pred) / y)
        porcentaje_buenas = 100 * np.mean(np.abs(y - y_pred) < 500000)

        resultados.append({
            'Cluster': cluster_id,
            'MAE': mae,
            'RMSE': rmse,
            'Error Relativo Promedio': relative_error,
            '% Error < $500,000': porcentaje_buenas,
            'N': len(df_cluster)
        })

    resultados_df = pd.DataFrame(resultados)

    # Crear el nuevo DataFrame con las columnas solicitadas
    arriendo_data_ubicacion = arriendo_df[['Barrio', 'Precio_ubicacion', 'Precio_m2_ubicacion']].copy()

    # Mostrar una vista previa
    arriendo_data_ubicacion.head()
    venta_df = preprocesor_venta(venta_df,arriendo_data_ubicacion,kmeans)
    venta = venta_df[features]
    venta_df['Prediccion_Precio'] = model.predict(venta_df[features])
    venta_df = calcular_roi_anual(venta_df)


    # Convertir la columna a numérica primero para poder filtrar correctamente

    # Filtrar las propiedades con ROI anual mayor o igual al 15%
    venta_df = venta_df[venta_df['ROI_anual_%'] <= 10]

    # Asegúrate de que esta columna exista y esté en formato numérico
    venta_df['ROI_anual_%'] = pd.to_numeric(venta_df['ROI_anual_%'], errors='coerce')
    venta_df = venta_df.drop_duplicates(subset=['Enlace'])

    # Seleccionar top 20
    top_20 = venta_df.sort_values(by='ROI_anual_%', ascending=False).head(20)

    # Crear PDF
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'TOP 20 PROPIEDADES POR ROI ANUAL', ln=True, align='C')
            self.ln(5)

        def property_table(self, df):
            self.set_font("Arial", size=8)
            for i, row in df.iterrows():
                self.multi_cell(0, 6, f" Propiedad #{i+1}", 0, 1)
                for col, val in row.items():
                    self.multi_cell(0, 6, f"{col}: {val}", 0, 1)
                self.ln(4)

    # Generar y guardar PDF
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.property_table(top_20)
    pdf_bytes = pdf.output(dest='S').encode('latin1')  # FPDF devuelve str → convertir a bytes
    pdf_buffer = BytesIO(pdf_bytes)
    pdf_buffer.seek(0)

    # Leer como binario para MongoDB
    contenido_pdf = Binary(pdf_buffer.read())

    return contenido_pdf