
import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from geopy.geocoders import Nominatim

st.set_page_config(
    page_title="Generador de Rutas",
    layout="wide"
)

st.title("🚗 Generador de Rutas")

try:

    clientes = pd.read_csv(
        "clientes.csv",
        sep=";"
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

except Exception as e:

    st.error(
        f"Error cargando clientes.csv: {e}"
    )

    st.stop()


def obtener_coordenadas(direccion):

    try:

        geolocator = Nominatim(
            user_agent="generador_rutas"
        )

        location = geolocator.geocode(
            direccion
        )

        if location:

            return (
                location.latitude,
                location.longitude
            )

        return None, None

    except:

        return None, None


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


st.subheader(
    "📍 Dirección de Inicio"
)

direccion_inicio = st.text_input(
    "Ingrese la dirección desde donde iniciará la ruta",
    placeholder="Ej: Cra 7 #72-41 Bogotá"
)

modo = st.radio(
    "Seleccione método de carga",
    [
        "Ingreso manual",
        "Cargar archivo CSV"
    ]
)

codigos = []

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

if st.button(
    "Generar Ruta"
):

    if not direccion_inicio:

        st.warning(
            "Debe ingresar una dirección de inicio."
        )

        st.stop()

    lat_inicio, lon_inicio = (
        obtener_coordenadas(
            direccion_inicio
        )
    )

    if lat_inicio is None:

        st.error(
            "No fue posible encontrar la dirección."
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

    seleccionados = (
        seleccionados
        .dropna(
            subset=["lat", "lon"]
        )
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
        seleccionados
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
            "Ruta Optimizada"
        )

        st.dataframe(
            ruta
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
