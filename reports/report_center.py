import streamlit as st
from reports.excel_report import build_excel
from reports.word_report import build_word
from reports.pdf_report import build_pdf
from reports.ppt_report import build_ppt

def render(df):
    st.subheader("Centro de informes")
    st.caption("Genera archivos con los filtros aplicados actualmente.")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Descargar Excel ejecutivo", build_excel(df),
                           "KOA_Analisis_Ejecutivo.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
        st.download_button("Descargar Word ejecutivo", build_word(df),
                           "KOA_Informe_Ejecutivo.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           use_container_width=True)
    with c2:
        st.download_button("Descargar PowerPoint ejecutivo", build_ppt(df),
                           "KOA_Presentacion_Ejecutiva.pptx",
                           "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                           use_container_width=True)
        st.download_button("Descargar PDF ejecutivo", build_pdf(df),
                           "KOA_Informe_Ejecutivo.pdf",
                           "application/pdf", use_container_width=True)
