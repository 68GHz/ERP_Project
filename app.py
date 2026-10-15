import streamlit as st
from shared_erp import CATALOG, apply_green_theme_css

# ==========================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==========================================
st.set_page_config(
    page_title="ERP de Inventarios y Predicción",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilos tema verde y blanco
apply_green_theme_css()

# Barra lateral informativa
st.sidebar.title("Sistema ERP")
st.sidebar.markdown("**Módulos de Productos**")
for pid, pdata in CATALOG.items():
    st.sidebar.page_link(pdata["page_file"], label=f"{pdata['name']}")

st.sidebar.markdown("---")
st.sidebar.caption("Modelo de Revisión Continua (Q, R) con factores estocásticos de Yahoo Finance.")

# Contenido principal
st.title("Sistema ERP: Gestión y Predicción de Inventarios")
st.markdown(
    "Bienvenido al panel central del sistema ERP. Seleccione el módulo de producto que desea gestionar "
    "para acceder a su análisis dinámico de demanda, optimización de lote económico (Q*) y política de reposición continua (PR, SS, T)."
)

st.markdown("---")
st.subheader("Catálogo de Productos Disponibles")

col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]

for idx, (pid, pdata) in enumerate(CATALOG.items()):
    with cols[idx]:
        st.markdown(
            f"""
            <div class="module-nav-card">
                <h3>{pdata['name']}</h3>
                <p><strong>Código:</strong> {pid}<br>
                <strong>Categoría:</strong> {pdata['category']}<br>
                <strong>Activo de Mercado:</strong> {pdata['ticker']}<br>
                <strong>Precio Unitario:</strong> ${pdata['unit_price']:.2f} USD</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.page_link(
            pdata["page_file"],
            label=f"Abrir Módulo de {pdata['name']}",
            use_container_width=True
        )

st.markdown("---")
st.subheader("Fundamentos del Modelo Operativo")
st.markdown(
    """
    Cada módulo de producto opera de forma independiente e implementa:
    - **Demanda Proyectada Dinámica (D):** Ajustada en tiempo real mediante variaciones de mercado de Yahoo Finance ponderadas por la sensibilidad del producto.
    - **Optimización Económica (Q*):** Cálculo exacto del Lote Económico que minimiza los costos anuales de emisión de pedidos y almacenamiento.
    - **Política de Reposición Continua (PR, SS, T):** Cálculo automático del Punto de Reorden considerando el Lead Time del proveedor y stock de seguridad, junto con el tiempo de ciclo entre órdenes.
    - **Alertas de Desabasto:** Notificación inmediata cuando la existencia física cae por debajo del Punto de Reorden para disparar la orden de compra.
    """
)