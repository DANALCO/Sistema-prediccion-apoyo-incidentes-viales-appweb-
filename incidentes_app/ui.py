"""Pequenos envoltorios para que la app funcione igual en versiones distintas de Streamlit."""

import streamlit as st


def grafico(fig, key=None):
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except TypeError:                                   # Streamlit mas antiguo
        st.plotly_chart(fig, use_container_width=True, key=key)


def tabla(df, **kw):
    try:
        return st.dataframe(df, width="stretch", **kw)
    except TypeError:
        return st.dataframe(df, use_container_width=True, **kw)


def boton_descarga(etiqueta, datos, nombre, mime, key):
    try:
        st.download_button(etiqueta, datos, file_name=nombre, mime=mime, key=key, width="stretch")
    except TypeError:
        st.download_button(etiqueta, datos, file_name=nombre, mime=mime, key=key, use_container_width=True)


def selector(etiqueta, opciones, key, help=None):
    """Selector de una opcion, en fila (botones tipo «pastilla»); en Streamlit antiguo, botones de radio."""
    if hasattr(st, "segmented_control"):
        st.segmented_control(etiqueta, opciones, key=key, selection_mode="single", help=help)
    else:
        st.radio(etiqueta, opciones, key=key, horizontal=True, help=help)


def boton(etiqueta, ancho_completo=True, **kw):
    """st.button que ocupa todo el ancho de su columna (con salida de emergencia para Streamlit antiguo)."""
    if ancho_completo:
        try:
            return st.button(etiqueta, width="stretch", **kw)
        except TypeError:
            return st.button(etiqueta, use_container_width=True, **kw)
    return st.button(etiqueta, **kw)
