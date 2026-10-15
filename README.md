# Mini-ERP de Gestión y Predicción de Inventarios

Sistema ERP ligero desarrollado en **Python** con **Streamlit**, enfocado en la gestión optimizada de inventarios y el pronóstico de compras mediante un **Modelo de Revisión Continua (Q, R)** acoplado a indicadores financieros dinámicos en tiempo real vía **Yahoo Finance (`yfinance`)**.

---

## 1. Guía de Instalación y Puesta en Marcha

### Requisitos Previos
- **Python**: Versión 3.10 o superior (compatible y probado en Windows con Python 3.13).
- Conexión a Internet (para la consulta en tiempo real de Yahoo Finance; la app cuenta con modo resiliencia en caso de fallos de red).

---

### Paso 1: Clonar o Situarse en el Directorio del Proyecto
Abre tu terminal (PowerShell o CMD) en la ruta del proyecto:
```powershell
cd c:\Users\user\Desktop\ERP_Project
```

---

### Paso 2: Instalación de Dependencias
Instala los paquetes necesarios definidos en `requirements.txt`:
```powershell
pip install -r requirements.txt
```

> **Nota para entornos con múltiples versiones de Python en Windows:**  
> Si tu comando `pip` apunta a una versión específica (por ejemplo Python 3.13) mientras `python` apunta a otra (por ejemplo Python 3.14), instala las dependencias directamente con el lanzador `py`:
> ```powershell
> py -3.13 -m pip install -r requirements.txt
> ```

Las dependencias principales son:
- `streamlit`: Servidor y framework web de interfaz interactiva.
- `yfinance`: Conector a Yahoo Finance para variaciones de mercado.
- `plotly`: Motor de renderizado de gráficos vectoriales interactivos.
- `pandas` y `numpy`: Modelado numérico y manipulación de series temporales.

---

### Paso 3: Iniciar la Aplicación

Para arrancar el servidor web local de Streamlit, ejecuta:

```powershell
py -3.13 -m streamlit run app.py
```
*(O simplemente `streamlit run app.py` si tu ejecutable de Streamlit está en el PATH de tu sistema).*

Una vez iniciado, la terminal indicará la URL local:
```text
Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```
Abre tu navegador web en `http://localhost:8501`.

---

## 2. Guía Funcional y Operativa del ERP

### Estructura del Proyecto

El sistema adopta la arquitectura multipágina nativa de Streamlit:

```text
ERP_Project/
├── .streamlit/
│   └── config.toml               # Configuración del tema visual (Light, alto contraste)
├── pages/                        # Módulos individuales por producto
│   ├── 1_Laptops_Corporativas.py # SKU PROD-001 (Tecnología / IT)
│   ├── 2_Bobinas_de_Acero.py     # SKU PROD-002 (Materiales Industriales)
│   └── 3_Cafe_Gourmet.py         # SKU PROD-003 (Agroindustria / Retail)
├── app.py                        # Panel central de inicio y catálogo
├── shared_erp.py                 # Motor matemático, ingesta de datos y componentes UI
├── requirements.txt              # Lista de dependencias del entorno
└── README.md                     # Documentación técnica y funcional
```

---

### Catálogo de Productos y Activos de Mercado

El sistema monitorea 3 categorías de productos representativas:

| Código | Producto | Categoría | Ticker Yahoo Finance | Justificación del Activo |
| :--- | :--- | :--- | :--- | :--- |
| **PROD-001** | Laptops Corporativas Pro 15" | Tecnología / IT | `^GSPC` (S&P 500) | Proxy macroeconómico de inversión de capital y confianza empresarial. |
| **PROD-002** | Bobina de Acero Estructural | Materiales Industriales | `HG=F` (Cobre/Metales) | Indicador adelantado de actividad fabril y construcción. |
| **PROD-003** | Café Gourmet en Grano (Quintales) | Agroindustria / Retail | `KC=F` (Futuros Café) | Commodity directo con volatilidad estacional de precios. |

---

### Fundamentos Matemáticos y Módulos del Sistema

#### Módulo 1: Optimización Económica ($Q^*$)

1. **Demanda Proyectada Dinámica ($D$):**
   La demanda anual base ($D_{\text{base}}$) se ajusta con la variación porcentual del activo en el período seleccionado ($\Delta M$), ponderada por la elasticidad o sensibilidad ($\beta$):
   $$D = \max\left(1, \; D_{\text{base}} \times (1 + \beta \cdot \Delta M)\right)$$

2. **Costo Total Formal ($CT$):**
   Calcula la erogación total anual considerando adquisición y costos operativos:
   $$CT = \underbrace{(D \cdot \text{Precio})}_{\text{Costo de Adquisición}} + \underbrace{\left(\frac{D}{Q} \cdot CP\right)}_{\text{Costo de Pedido}} + \underbrace{\left(\frac{Q}{2} \cdot Cal\right)}_{\text{Costo de Almacenamiento}}$$
   - **$CP$ (Costo de Pedido):** Costo fijo administrativo/flete por emitir una orden.
   - **$Cal$ (Costo de Almacenamiento):** Costo de tenencia por unidad/año (mermas, espacio, seguros).

3. **Lote Económico Óptimo ($Q^*$):**
   Minimiza los costos operativos en la intersección exacta de las curvas secundarias:
   $$Q^* = \sqrt{\frac{2 \cdot D \cdot CP}{Cal}}$$

---

#### Módulo 2: Política de Reposición Continua (PR, SS, T)

1. **Punto de Reorden ($PR$):**
   Nivel de inventario que dispara una orden de reabastecimiento:
   $$PR = (\bar{d} \cdot T_{\text{Proveedor}}) + SS$$
   Donde $\bar{d} = \frac{D}{365}$ es la demanda diaria promedio y $T_{\text{Proveedor}}$ es el Lead Time en días.

2. **Stock de Seguridad ($SS$):**
   Colchón de reserva para amortiguar retrasos del proveedor o picos inesperados de demanda.

3. **Tiempo de Ciclo ($T$):**
   Periodicidad promedio óptima entre órdenes consecutivas:
   $$T = \left(\frac{Q^*}{D}\right) \cdot 365 \text{ días}$$

---

### Interpretación de Alertas de Inventario

La aplicación evalúa el **Stock Actual Físico** contra el **Punto de Reorden ($PR$)**:

- **Alerta Crítica (Borde Rojo):**
  $$\text{Stock Actual} \le PR$$
  *Indica que el inventario penetró el umbral de seguridad. Se debe emitir una orden de compra inmediata por exactamente $Q^*$ unidades.*
- **Atención Preventiva (Borde Ámbar):**
  $$PR < \text{Stock Actual} \le 1.20 \times PR$$
  *El inventario está a menos del 20% sobre el punto de reorden. La app calcula los días estimados de holgura restante antes del reabastecimiento.*
- **Inventario Saludable (Borde Verde):**
  $$\text{Stock Actual} > 1.20 \times PR$$
  *Operación con margen adecuado. No se requiere intervención inmediata.*

---

### Interpretación del Gráfico Interactivo de Costos

El gráfico en cada página de producto utiliza una terna cromática de alto contraste:

- **Línea Roja Discontinua:** **Costo Anual de Pedido** $\left(\frac{D}{Q} \cdot CP\right)$. Decrece a medida que el tamaño de lote aumenta (menos órdenes al año).
- **Línea Azul Discontinua:** **Costo Anual de Almacenamiento** $\left(\frac{Q}{2} \cdot Cal\right)$. Crece linealmente a mayor tamaño de lote (más inventario promedio).
- **Línea Verde Continua:** **Costos Variables Operativos** (Pedido + Almacenamiento). Presenta una parábola convexa cuyo mínimo coincide con la intersección de las líneas roja y azul.
- **Marcador Diamante Negro:** Posición exacta del **Lote Óptimo $Q^*$** con su costo mínimo asociado.

---

### Navegación y Ajuste de Parámetros en Tiempo Real

1. **Panel Central ([app.py](file:///c:/Users/user/Desktop/ERP_Project/app.py)):** Muestra el catálogo general de los 3 productos con accesos directos por tarjeta o menú lateral.
2. **Barra Lateral en cada Producto:** Permite modificar interactivamente:
   - Precio de compra unitario.
   - Demanda anual base ($D$).
   - Costo de orden ($CP$) y almacenamiento ($Cal$).
   - Stock actual físico, Lead time ($T_{\text{Proveedor}}$) y Stock de Seguridad ($SS$).
   - Ticker de Yahoo Finance, ventana histórica de análisis y elasticidad ($\beta$).
3. Todos los cálculos, alertas y gráficos se recalculan en tiempo real sin recargar la página.

