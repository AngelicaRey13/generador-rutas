
import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from streamlit_geolocation import streamlit_geolocation
import glob

st.set_page_config(
    page_title="Generador de Rutas",
    layout="wide"
)

st.title("🏍️ Generador de Rutas S&R")


# ----------------------------
# CARGAR BASE DE CLIENTES
# ----------------------------

try:

    archivos_clientes = glob.glob(
        "clientes*.csv"
    )

    if len(archivos_clientes) == 0:

        raise Exception(
            "No se encontraron archivos que inicien por 'clientes'"
        )

    clientes = pd.concat(
        [
            pd.read_csv(
                archivo,
                sep=";"
            )
            for archivo in archivos_clientes
        ],
        ignore_index=True
    )

    clientes.columns = (
        clientes.columns
        .str.strip()
        .str.lower()
    )

    clientes["codigo_cliente"] = (
        clientes["codigo_cliente"]
        .astype(str)
        .str.strip()
    )

    st.success(
        f"Base cargada correctamente. "
        f"Archivos encontrados: {len(archivos_clientes)} | "
        f"Registros: {len(clientes):,}"
    )

except Exception as e:

    st.error(
        f"Error cargando bases de clientes: {e}"
    )

    st.stop()
clientes["lat"] = (
    clientes["lat"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)

clientes["lon"] = (
    clientes["lon"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)

clientes["lat"] = pd.to_numeric(
    clientes["lat"],
    errors="coerce"
)

clientes["lon"] = pd.to_numeric(
    clientes["lon"],
    errors="coerce"
)

clientes = clientes.dropna(
    subset=["lat", "lon"]
)
# ----------------------------
# UBICACIÓN ACTUAL
# ----------------------------

st.subheader("📍 Ubicación actual")

location = streamlit_geolocation()

lat_inicio = None
lon_inicio = None

if location:

    lat_inicio = location.get("latitude")
    lon_inicio = location.get("longitude")

    if lat_inicio is not None and lon_inicio is not None:

        st.success(
            "Ubicación obtenida correctamente"
        )

        st.write(
            f"Latitud: {lat_inicio}"
        )

        st.write(
            f"Longitud: {lon_inicio}"
        )

else:

    st.info(
        "Permita el acceso a la ubicación cuando el navegador lo solicite."
    )

# ----------------------------
# DISTANCIA
# ----------------------------

def distancia(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371

    dlat = radians(
        lat2 - lat1
    )

    dlon = radians(
        lon2 - lon1
    )

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c

# ----------------------------
# OPTIMIZAR RUTA
# ----------------------------

def optimizar_ruta(
    df,
    lat_inicio,
    lon_inicio
):

    pendientes = df.copy()

    ruta = []

    lat_actual = lat_inicio
    lon_actual = lon_inicio

    while len(pendientes) > 0:

        pendientes["distancia"] = pendientes.apply(
            lambda x: distancia(
                lat_actual,
                lon_actual,
                x["lat"],
                x["lon"]
            ),
            axis=1
        )

        siguiente = pendientes.loc[
            pendientes["distancia"].idxmin()
        ]

        ruta.append(
            siguiente.to_dict()
        )

        lat_actual = siguiente["lat"]
        lon_actual = siguiente["lon"]

        pendientes = pendientes.drop(
            siguiente.name
        )

    return pd.DataFrame(ruta)

# ----------------------------
# GENERAR LINK
# ----------------------------

def generar_link(
    ruta,
    lat_inicio,
    lon_inicio
):

    destinos = []

    for _, fila in ruta.iterrows():

        destinos.append(
            f"{fila['lat']},{fila['lon']}"
        )

    return (
        f"https://www.google.com/maps/dir/"
        f"{lat_inicio},{lon_inicio}/"
        + "/".join(destinos)
    )

# ----------------------------
# INGRESO DE CÓDIGOS
# ----------------------------

st.subheader(
    "📋 Seleccione método de carga"
)

modo = st.radio(
    "",
    [
        "Ingreso manual",
        "Cargar archivo CSV"
    ]
)

codigos = []

# ----------------------------
# INGRESO MANUAL
# ----------------------------

if modo == "Ingreso manual":

 texto = st.text_area(
    "Ingrese un código por línea"
  )
    if texto:

        codigos = [
            x.strip()
            for x in texto.split("\n")
            if x.strip()
        ]

# ----------------------------
# CARGAR ARCHIVO
# ----------------------------

else:

   archivo = st.file_uploader(
    "Seleccione archivo CSV",
    type=["csv"]
)

    if archivo:

        try:

            df_codigos = pd.read_csv(
                archivo,
                sep=";"
            )

        except:

            df_codigos = pd.read_csv(
                archivo
            )

        codigos = (
            df_codigos.iloc[:, 0]
            .astype(str)
            .str.strip()
            .tolist()
        )

# ----------------------------
# BOTONES
# ----------------------------

col1, col2 = st.columns(2)

with col1:
    generar = st.button(
        "🚀 Generar Ruta",
        use_container_width=True
    )

with col2:
    limpiar = st.button(
        "🧹 Limpiar Consulta",
        use_container_width=True
    )

if limpiar:
    st.rerun()

if generar:

    if lat_inicio is None or lon_inicio is None:

        st.warning(
            "Debe permitir el acceso a la ubicación."
        )

        st.stop()

    if len(codigos) == 0:

        st.warning(
            "Debe ingresar al menos un código."
        )

        st.stop()

    seleccionados = clientes[
        clientes["codigo_cliente"]
        .isin(codigos)
    ]

    seleccionados = seleccionados.dropna(
        subset=["lat", "lon"]
    )

    encontrados = len(
        seleccionados
    )

    no_encontrados = list(
        set(codigos)
        -
        set(
            seleccionados[
                "codigo_cliente"
            ]
            .astype(str)
        )
    )

    st.info(
        f"Se solicitaron {len(codigos)} cuentas."
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Cuentas encontradas",
            encontrados
        )

    with col2:

        st.metric(
            "Cuentas no encontradas",
            len(no_encontrados)
        )

    if encontrados > 0:

        st.success(
            f"Se encontraron {encontrados} cuentas."
        )

    if len(no_encontrados) > 0:

        st.warning(
            "Cuentas no encontradas"
        )

        st.write(
            no_encontrados
        )

    st.subheader(
        "Clientes encontrados"
    )

    st.dataframe(
        seleccionados,
        use_container_width=True
    )

    if encontrados > 20:

        st.warning(
            "Google Maps puede limitar rutas con muchas paradas."
        )

    if encontrados > 0:

        ruta = optimizar_ruta(
            seleccionados,
            lat_inicio,
            lon_inicio
        )

        st.subheader(
            "🛣️ Ruta Optimizada"
        )

        st.dataframe(
            ruta,
            use_container_width=True
        )

        link = generar_link(
            ruta,
            lat_inicio,
            lon_inicio
        )

        st.link_button(
            "🗺️ Abrir Ruta en Google Maps",
            link
        )
