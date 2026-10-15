import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime

# ==========================================
# CATÁLOGO DE PRODUCTOS (SIN EMOJIS)
# ==========================================
CATALOG = {
    "PROD-001": {
        "name": "Laptops Corporativas Pro 15\"",
        "page_file": "pages/1_Laptops_Corporativas.py",
        "category": "Tecnología / IT",
        "ticker": "^GSPC",
        "unit_price": 850.0,
        "base_demand": 1200,
        "order_cost": 250.0,
        "holding_cost": 45.0,
        "lead_time_days": 12,
        "safety_stock": 50,
        "current_stock": 85,
        "elasticity": 0.8
    },
    "PROD-002": {
        "name": "Bobina de Acero Estructural",
        "page_file": "pages/2_Bobinas_de_Acero.py",
        "category": "Materiales Industriales",
        "ticker": "HG=F",
        "unit_price": 120.0,
        "base_demand": 3500,
        "order_cost": 400.0,
        "holding_cost": 18.0,
        "lead_time_days": 20,
        "safety_stock": 100,
        "current_stock": 240,
        "elasticity": 1.2
    },
    "PROD-003": {
        "name": "Café Gourmet en Grano (Quintales)",
        "page_file": "pages/3_Cafe_Gourmet.py",
        "category": "Agroindustria / Retail",
        "ticker": "KC=F",
        "unit_price": 65.0,
        "base_demand": 5000,
        "order_cost": 150.0,
        "holding_cost": 8.0,
        "lead_time_days": 8,
        "safety_stock": 60,
        "current_stock": 380,
        "elasticity": 0.6
    }
}

# ==========================================
# INGESTA DINÁMICA DE MERCADO (yfinance)
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_market_variation(ticker: str, period: str = "1mo") -> tuple[float, str, bool]:
    """
    Descarga cotizaciones históricas vía yfinance y calcula la variación porcentual.
    Maneja excepciones de red o activos inválidos con fallback neutral (0.0%).
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        
        if hist.empty or len(hist) < 2:
            return 0.0, f"Sin datos suficientes para {ticker}. Se asume variación neutral (0.0%).", True
        
        initial_price = float(hist["Close"].iloc[0])
        latest_price = float(hist["Close"].iloc[-1])
        
        if initial_price <= 0:
            return 0.0, "Precio base no positivo recibido de la API.", True
            
        pct_change = (latest_price - initial_price) / initial_price
        return pct_change, f"Mercado '{ticker}' sincronizado con éxito ({period}).", False
        
    except Exception as e:
        return 0.0, f"Conexión no disponible con Yahoo Finance ({ticker}): {str(e)}. Modo resiliencia activo.", True

# ==========================================
# MÓDULOS MATEMÁTICOS DE LOGÍSTICA
# ==========================================
def calculate_dynamic_demand(base_demand: float, market_pct_change: float, elasticity: float) -> float:
    """Calcula la Demanda Proyectada Dinámica (D) con factor de mercado."""
    adjusted = base_demand * (1.0 + (elasticity * market_pct_change))
    return max(1.0, round(adjusted, 2))

def calculate_optimal_q(demand: float, cp: float, cal: float) -> float:
    """Calcula el Lote Económico de Pedido Óptimo: Q* = sqrt((2 * D * CP) / Cal)."""
    if demand <= 0 or cp <= 0 or cal <= 0:
        return 0.0
    return float(np.sqrt((2.0 * demand * cp) / cal))

def calculate_total_cost(demand: float, q: float, unit_price: float, cp: float, cal: float) -> tuple[float, float, float, float]:
    """
    Calcula el Costo Total formal:
    CT = (D * Precio) + (D/Q * CP) + (Q/2 * Cal)
    """
    if q <= 0:
        return 0.0, 0.0, 0.0, 0.0
    cost_acquisition = demand * unit_price
    cost_ordering = (demand / q) * cp
    cost_holding = (q / 2.0) * cal
    cost_total = cost_acquisition + cost_ordering + cost_holding
    return cost_acquisition, cost_ordering, cost_holding, cost_total

def calculate_reorder_point(demand: float, lead_time_days: float, safety_stock: float) -> float:
    """Punto de Reorden: PR = (Demanda Diaria Promedio * T Proveedor) + SS."""
    daily_demand = demand / 365.0
    return (daily_demand * lead_time_days) + safety_stock

def calculate_cycle_time(q_opt: float, demand: float) -> float:
    """Tiempo de Ciclo óptimo entre órdenes en días: T = (Q* / D) * 365."""
    if demand <= 0:
        return 0.0
    return (q_opt / demand) * 365.0

def generate_cost_curves(demand: float, unit_price: float, cp: float, cal: float, q_opt: float) -> pd.DataFrame:
    """Genera las curvas de costos secundarias y de Costo Total en función de Q."""
    q_min = max(1, int(q_opt * 0.2))
    q_max = max(10, int(q_opt * 2.3))
    q_range = np.linspace(q_min, q_max, 250)

    ordering_curve = (demand / q_range) * cp
    holding_curve = (q_range / 2.0) * cal
    inventory_costs = ordering_curve + holding_curve
    total_costs = (demand * unit_price) + inventory_costs

    return pd.DataFrame({
        "Q": q_range,
        "Costo_Pedido": ordering_curve,
        "Costo_Almacenamiento": holding_curve,
        "Costos_Operativos_Inv": inventory_costs,
        "Costo_Total": total_costs
    })

# ==========================================
# ESTILOS CSS DE ALTO CONTRASTE (ESCALA DE GRISES + VERDE)
# ==========================================
def apply_green_theme_css():
    st.markdown(
        """
        <style>
        /* Tipografía nítida con escala de grises de alto contraste */
        body, .main, [data-testid="stAppViewContainer"] {
            background-color: #ffffff;
            color: #111827 !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #111827 !important;
            font-weight: 700;
            letter-spacing: -0.01em;
        }

        p, span, label, div {
            color: #1f2937;
        }

        /* Sidebar con escala de grises limpia */
        [data-testid="stSidebar"] {
            background-color: #f9fafb !important;
            border-right: 1px solid #e5e7eb;
        }
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3 {
            color: #111827 !important;
        }

        /* Contenedores de alerta accesibles y con contraste nítido */
        .alert-box {
            padding: 14px 18px;
            border-radius: 8px;
            margin-bottom: 1.2rem;
            font-size: 0.96rem;
            line-height: 1.5;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        .alert-box-critical {
            background-color: #fef2f2;
            border-left: 5px solid #dc2626;
            border-top: 1px solid #fecaca;
            border-right: 1px solid #fecaca;
            border-bottom: 1px solid #fecaca;
            color: #991b1b !important;
        }
        .alert-box-critical strong, .alert-box-critical span {
            color: #991b1b !important;
        }

        .alert-box-warning {
            background-color: #fffbeb;
            border-left: 5px solid #d97706;
            border-top: 1px solid #fde68a;
            border-right: 1px solid #fde68a;
            border-bottom: 1px solid #fde68a;
            color: #92400e !important;
        }
        .alert-box-warning strong, .alert-box-warning span {
            color: #92400e !important;
        }

        .alert-box-success {
            background-color: #f0fdf4;
            border-left: 5px solid #16a34a;
            border-top: 1px solid #bbf7d0;
            border-right: 1px solid #bbf7d0;
            border-bottom: 1px solid #bbf7d0;
            color: #14532d !important;
        }
        .alert-box-success strong, .alert-box-success span {
            color: #14532d !important;
        }

        .alert-box-info {
            background-color: #f9fafb;
            border-left: 5px solid #16a34a;
            border-top: 1px solid #e5e7eb;
            border-right: 1px solid #e5e7eb;
            border-bottom: 1px solid #e5e7eb;
            color: #111827 !important;
        }
        .alert-box-info strong, .alert-box-info span {
            color: #111827 !important;
        }

        /* Tarjeta de Costo Total con contraste garantizado */
        .cost-card {
            background-color: #f0fdf4;
            border: 1.5px solid #86efac;
            border-radius: 8px;
            padding: 14px 18px;
            margin-top: 14px;
            color: #111827 !important;
            font-size: 1.02rem;
            box-shadow: 0 1px 3px rgba(22, 163, 74, 0.08);
        }
        .cost-card strong {
            color: #15803d !important;
            font-weight: 800;
        }

        /* Tarjetas de navegación principal */
        .module-nav-card {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-top: 3px solid #16a34a;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            transition: all 0.15s ease-in-out;
        }
        .module-nav-card:hover {
            border-color: #16a34a;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            transform: translateY(-2px);
        }
        .module-nav-card h3 {
            color: #111827 !important;
            margin-top: 0;
            margin-bottom: 8px;
        }
        .module-nav-card p {
            color: #4b5563 !important;
            margin-bottom: 12px;
            font-size: 0.94rem;
        }
        .module-nav-card strong {
            color: #111827 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# ==========================================
# RENDERIZADOR DEL MÓDULO POR PÁGINA DE PRODUCTO
# ==========================================
def render_product_page(product_id: str):
    apply_green_theme_css()
    prod_info = CATALOG[product_id]

    # Barra lateral de configuración del producto
    st.sidebar.markdown(f"## {prod_info['name']}")
    st.sidebar.markdown("**Parámetros de Entrada**")

    st.sidebar.markdown("### 1. Variables Económicas")
    unit_price = st.sidebar.number_input(
        "Precio Unitario ($)",
        min_value=0.1, max_value=50000.0, value=float(prod_info["unit_price"]), step=10.0,
        help="Costo directo unitario de compra."
    )
    base_demand = st.sidebar.number_input(
        "Demanda Anual Base (D)",
        min_value=10, max_value=200000, value=int(prod_info["base_demand"]), step=50,
        help="Demanda anual proyectada sin factor de mercado."
    )
    cp = st.sidebar.number_input(
        "Costo de Pedido (CP) [$ por orden]",
        min_value=1.0, max_value=10000.0, value=float(prod_info["order_cost"]), step=10.0,
        help="Costo fijo administrativo y logístico de emitir una orden."
    )
    cal = st.sidebar.number_input(
        "Costo de Almacenamiento (Cal) [$/ud/año]",
        min_value=0.1, max_value=5000.0, value=float(prod_info["holding_cost"]), step=1.0,
        help="Costo anual de mantener una unidad en bodega."
    )

    st.sidebar.markdown("### 2. Política de Reposición")
    current_stock = st.sidebar.number_input(
        "Stock Actual en Bodega (Uds)",
        min_value=0, max_value=100000, value=int(prod_info["current_stock"]), step=5,
        help="Nivel físico actual disponible en almacén."
    )
    lead_time = st.sidebar.number_input(
        "T Proveedor (Lead Time) [Días]",
        min_value=1, max_value=180, value=int(prod_info["lead_time_days"]), step=1,
        help="Días que tarda el proveedor en entregar el pedido."
    )
    safety_stock = st.sidebar.number_input(
        "Stock de Seguridad (SS) [Uds]",
        min_value=0, max_value=10000, value=int(prod_info["safety_stock"]), step=5,
        help="Inventario colchón para evitar desabasto."
    )

    st.sidebar.markdown("### 3. Factor de Mercado")
    ticker_input = st.sidebar.text_input("Ticker Yahoo Finance", value=prod_info["ticker"])
    market_window = st.sidebar.selectbox("Ventana Temporal", ["5d", "1mo", "3mo", "6mo", "1y"], index=1)
    elasticity = st.sidebar.slider("Sensibilidad (Beta)", min_value=0.0, max_value=3.0, value=float(prod_info["elasticity"]), step=0.1)

    # Botón de retorno al inicio
    st.sidebar.markdown("---")
    st.sidebar.page_link("app.py", label="Volver a Inicio / Catálogo General")

    # Ejecución de cálculos
    with st.spinner("Sincronizando indicador de mercado con Yahoo Finance..."):
        m_pct, m_msg, is_fallback = fetch_market_variation(ticker_input, market_window)

    d_din = calculate_dynamic_demand(base_demand, m_pct, elasticity)
    daily_d = d_din / 365.0
    q_opt = calculate_optimal_q(d_din, cp, cal)
    c_adq, c_ped, c_alm, ct_total = calculate_total_cost(d_din, q_opt, unit_price, cp, cal)
    pr_val = calculate_reorder_point(d_din, lead_time, safety_stock)
    cycle_t_days = calculate_cycle_time(q_opt, d_din)
    orders_year = d_din / q_opt if q_opt > 0 else 0

    # Encabezado principal
    st.title(f"Módulo: {prod_info['name']}")
    st.caption(f"Código: {product_id} | Categoría: {prod_info['category']} | Actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Notificación de mercado
    st.markdown(
        f"""
        <div class="alert-box alert-box-info">
            <strong>Estado de Mercado:</strong> {m_msg} | Variación observada: <strong>{m_pct * 100:+.2f}%</strong> (Beta = {elasticity})
        </div>
        """,
        unsafe_allow_html=True
    )

    # Alerta de inventario estricta basada en PR
    if current_stock <= pr_val:
        deficit = pr_val - current_stock
        st.markdown(
            f"""
            <div class="alert-box alert-box-critical">
                <strong>Alerta: Stock actual por debajo del Punto de Reorden. Emitir orden de compra de {round(q_opt)} unidades de inmediato.</strong><br>
                <span>Stock Actual: <strong>{current_stock} uds</strong> | Punto de Reorden (PR): <strong>{pr_val:.1f} uds</strong> | Déficit: <strong>{deficit:.1f} uds</strong>.</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif current_stock <= (pr_val * 1.20):
        holgura_dias = ((current_stock - pr_val) / daily_d) if daily_d > 0 else 0
        st.markdown(
            f"""
            <div class="alert-box alert-box-warning">
                <strong>Atención Preventiva: Stock Próximo al Punto de Reorden.</strong><br>
                <span>Stock Actual: <strong>{current_stock} uds</strong> | PR: <strong>{pr_val:.1f} uds</strong> | Holgura estimada: <strong>{holgura_dias:.1f} días</strong> antes de requerir reabastecimiento.</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        superavit = current_stock - pr_val
        st.markdown(
            f"""
            <div class="alert-box alert-box-success">
                <strong>Inventario Saludable:</strong> El stock actual (<strong>{current_stock} uds</strong>) supera el Punto de Reorden (<strong>{pr_val:.1f} uds</strong>) con un margen de <strong>+{superavit:.1f} uds</strong>.
            </div>
            """,
            unsafe_allow_html=True
        )

    # Resultados en dos columnas
    col_econ, col_policy = st.columns(2)

    with col_econ:
        st.subheader("Módulo 1: Optimización Económica (Q*)")
        st.markdown("Minimización de costos anuales de pedido y mantenimiento de inventario.")

        e_c1, e_c2 = st.columns(2)
        e_c1.metric(
            label="Demanda Proyectada (D)",
            value=f"{d_din:,.0f} uds/año",
            delta=f"{m_pct*100:+.2f}% vs Base"
        )
        e_c2.metric(
            label="Lote Óptimo (Q*)",
            value=f"{q_opt:,.1f} uds",
            delta=f"{orders_year:.1f} órdenes/año"
        )

        st.markdown("##### Desglose Formal de Costo Total (CT)")
        st.latex(r"CT = (D \cdot \text{Precio}) + \left(\frac{D}{Q} \cdot CP\right) + \left(\frac{Q}{2} \cdot Cal\right)")

        ct1, ct2, ct3 = st.columns(3)
        ct1.metric("Costo Adquisición", f"${c_adq:,.2f}")
        ct2.metric("Costo Pedido (CP)", f"${c_ped:,.2f}")
        ct3.metric("Costo Almacén (Cal)", f"${c_alm:,.2f}")

        # Tarjeta con color de texto de alto contraste garantizado
        st.markdown(
            f"""
            <div class="cost-card">
                Costo Total Anual Mínimo (CT): <strong>${ct_total:,.2f} USD</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_policy:
        st.subheader("Módulo 2: Política de Reposición (PR, SS, T)")
        st.markdown("Definición paramétrica del modelo de Revisión Continua (Q, R).")

        p_c1, p_c2 = st.columns(2)
        p_c1.metric(
            label="Punto de Reorden (PR)",
            value=f"{pr_val:,.1f} uds",
            delta=f"{current_stock - pr_val:+.1f} vs Stock",
            delta_color="normal" if current_stock > pr_val else "inverse"
        )
        p_c2.metric(
            label="Tiempo de Ciclo (T)",
            value=f"{cycle_t_days:.1f} días",
            delta="Periodicidad óptima",
            delta_color="off"
        )

        st.markdown("##### Parámetros Operativos de Reposición")
        st.latex(r"PR = (\bar{d} \cdot T_{\text{Proveedor}}) + SS \quad \mid \quad T = \left(\frac{Q^*}{D}\right) \cdot 365")

        pr1, pr2, pr3 = st.columns(3)
        pr1.metric("T Proveedor", f"{lead_time} días")
        pr2.metric("Stock Seguridad (SS)", f"{safety_stock} uds")
        pr3.metric("Demanda Diaria", f"{daily_d:.2f} uds/día")

        if current_stock <= pr_val:
            badge_text = "REQUIERE COMPRA INMEDIATA"
        elif current_stock <= pr_val * 1.2:
            badge_text = "ESTADO DE VIGILANCIA"
        else:
            badge_text = "COBERTURA SALUDABLE"

        st.markdown(f"**Estado del Inventario:** {badge_text} | Stock Físico: **{current_stock} uds**")

    # Gráfico interactivo con alto contraste: Rojo, Verde, Azul
    st.markdown("---")
    st.markdown("### Curvas de Costos Secundarios y Punto de Minimización")
    st.write(
        "El tamaño de lote óptimo Q* se ubica en el punto exacto donde la curva del **Costo de Pedido (Rojo)** "
        "interseca la curva del **Costo de Almacenamiento (Azul)**, minimizando la curva de **Costos Operativos Variables (Verde)**."
    )

    df_curves = generate_cost_curves(d_din, unit_price, cp, cal, q_opt)

    fig = go.Figure()

    # 1. Curva Costo de Pedido (ROJO de alto contraste, línea discontinua)
    fig.add_trace(go.Scatter(
        x=df_curves["Q"],
        y=df_curves["Costo_Pedido"],
        mode="lines",
        name="Costo de Pedido (D/Q · CP)",
        line=dict(color="#dc2626", width=2.5, dash="dash")
    ))

    # 2. Curva Costo de Almacenamiento (AZUL de alto contraste, línea discontinua)
    fig.add_trace(go.Scatter(
        x=df_curves["Q"],
        y=df_curves["Costo_Almacenamiento"],
        mode="lines",
        name="Costo Almacenamiento (Q/2 · Cal)",
        line=dict(color="#2563eb", width=2.5, dash="dash")
    ))

    # 3. Curva Costos Operativos Variables (VERDE principal, línea sólida continua)
    fig.add_trace(go.Scatter(
        x=df_curves["Q"],
        y=df_curves["Costos_Operativos_Inv"],
        mode="lines",
        name="Costos Variables (Pedido + Almacén)",
        line=dict(color="#16a34a", width=3.2)
    ))

    # 4. Marcador en el Punto Óptimo Q* (Negro carbón con borde visible)
    fig.add_trace(go.Scatter(
        x=[q_opt],
        y=[c_ped + c_alm],
        mode="markers+text",
        name="Q* Óptimo (Intersección)",
        text=[f"  Q* = {q_opt:.1f} uds<br>  C.Inv = ${c_ped + c_alm:,.2f}"],
        textposition="top right",
        marker=dict(
            color="#111827",
            size=14,
            symbol="diamond",
            line=dict(color="#ffffff", width=2)
        )
    ))

    # Línea vertical guía de alta visibilidad
    fig.add_vline(
        x=q_opt,
        line_width=1.5,
        line_dash="dot",
        line_color="#4b5563",
        annotation_text=f"Q* = {q_opt:.1f}",
        annotation_position="bottom right"
    )

    fig.update_layout(
        title=f"Optimización de Costos de Inventario para {prod_info['name']}",
        xaxis_title="Tamaño del Lote de Pedido (Q) [Unidades]",
        yaxis_title="Costo Anual ($ USD)",
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(color="#111827"),
        xaxis=dict(
            gridcolor="#e5e7eb",
            zerolinecolor="#d1d5db",
            linecolor="#9ca3af"
        ),
        yaxis=dict(
            gridcolor="#e5e7eb",
            zerolinecolor="#d1d5db",
            linecolor="#9ca3af"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#e5e7eb",
            borderwidth=1
        ),
        template="plotly_white",
        height=500,
        margin=dict(l=40, r=40, t=80, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)
