import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import urllib.request

# --- 1. SETUP UI E CSS ---
st.set_page_config(page_title="Dashboard ESG - Créditos de Carbono", layout="wide", page_icon="🌿")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-green: #007A33;
        --bg-color: #F4F7F6;
    }
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
    }
    body, .stApp {
        background-color: #F4F7F6;
    }
    h1, h2, h3, h4 {
        color: #004D20 !important;
        font-family: 'Inter', sans-serif;
    }
    /* Sidebar Background */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
    }
    /* Labels for filters and titles */
    label, .st-emotion-cache-1yvjcxr label, div[data-testid="stWidgetLabel"] p {
        color: #7F8C8D !important;
        font-weight: 500;
    }
    /* Metric Cards - Forçando fundo branco e mesmo tamanho */
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border-radius: 15px !important;
        padding: 15px !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05) !important;
        border-left: 5px solid #007A33 !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    /* Metric card titles */
    [data-testid="stMetricLabel"] > div {
        color: #7F8C8D !important;
    }
    /* Metric values */
    [data-testid="stMetricValue"] > div {
        color: #004D20 !important;
        font-weight: 700;
    }
    /* Arredondamento dos Gráficos/Tabelas */
    .stPlotlyChart, [data-testid="stDataFrame"] {
        border-radius: 15px !important;
        overflow: hidden !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05) !important;
        background-color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. LOAD DATA (SILVER LAYER) ---
@st.cache_data
def load_data():
    # Resolve absolute path to the project root (one directory up from app.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    base_dir = os.path.join(project_root, "dados", "02.prata")
    
    # 1. Crop Yield
    df_crop = pd.read_csv(os.path.join(base_dir, "kaggle_crop_yield", "crop_yield_silver.csv"))
    # 2. Cobertura Brasil
    df_cob = pd.read_csv(os.path.join(base_dir, "mapbiomas", "prata_cobertura_brasil_nivel1.csv"))
    # 3. Desmatamento Estado/Bioma
    df_desm_est = pd.read_csv(os.path.join(base_dir, "mapbiomas", "prata_desmatamento_estado_bioma.csv"))
    # 4. Desmatamento Geral
    df_desm = pd.read_parquet(os.path.join(base_dir, "mapbiomas", "prata_desmatamento.parquet"))
    # 5. Pastagem
    df_past = pd.read_csv(os.path.join(base_dir, "mapbiomas", "prata_pastagem.csv"), low_memory=False)
    # 6. Chuva NASA
    df_chuva = pd.read_csv(os.path.join(base_dir, "nasa", "prata_nasa_chuva_estados_brasil.csv"), sep=';')
    # 7. SEEG
    df_seeg = pd.read_parquet(os.path.join(base_dir, "SEEG", "prata_seeg_all.parquet"))
    
    # Dicionário de UFs (Pedido do Usuário)
    mapa_uf = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia',
        'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás',
        'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
        'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco', 'PI': 'Piauí',
        'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul',
        'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'São Paulo',
        'SE': 'Sergipe', 'TO': 'Tocantins'
    }
    
    # Padronizar NASA
    df_chuva['ano'] = df_chuva['Ano']
    df_chuva['estado'] = df_chuva['UF'].map(mapa_uf).str.title()
    
    # Padronizar nomes nas bases (Title Case)
    if 'nome_estado' in df_past.columns:
        df_past['estado'] = df_past['nome_estado'].str.title()
    if 'nome_estado' in df_desm.columns:
        df_desm['estado'] = df_desm['nome_estado'].str.title()
    if 'estado' in df_seeg.columns:
        df_seeg['estado'] = df_seeg['estado'].str.title()
        
    return df_crop, df_cob, df_desm_est, df_desm, df_past, df_chuva, df_seeg

with st.spinner("Carregando Camada Silver..."):
    df_crop, df_cob, df_desm_est, df_desm, df_past, df_chuva, df_seeg = load_data()

@st.cache_data
def load_geojson():
    url_geojson = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    with urllib.request.urlopen(url_geojson) as url:
        return json.loads(url.read().decode())

brazil_geojson = load_geojson()

# --- 3. SIDEBAR (FILTROS GLOBAIS) ---
st.sidebar.title("🌿 ESG Dashboard")
st.sidebar.markdown("---")

# Menus de Navegação
page = st.sidebar.radio("Navegação", [
    "Visão Executiva", 
    "Emissões & Clima", 
    "Uso da Terra & Risco", 
    "Pastagens & Carbono"
])

st.sidebar.markdown("---")

# Opções de Filtro Dinâmicas (Baseado no SEEG por ser o mais amplo)
anos_disponiveis = sorted(df_seeg['ano'].unique(), reverse=True)
estados_disponiveis = ["Todos"] + sorted(df_seeg['estado'].dropna().unique())
biomas_disponiveis = ["Todos"] + sorted(df_seeg['bioma'].dropna().unique())

f_ano = st.sidebar.slider("Ano", min_value=int(min(anos_disponiveis)), max_value=int(max(anos_disponiveis)), value=(2010, 2022))
f_estado = st.sidebar.selectbox("Estado (UF)", estados_disponiveis)
f_bioma = st.sidebar.selectbox("Bioma", biomas_disponiveis)

st.sidebar.markdown("---")

# Filtros de Emissão em Cascata
f_setor1 = st.sidebar.selectbox("Setor de Emissão", ["Todos"] + sorted(df_seeg['setor_nivel1'].dropna().unique()))

opts_setor2 = ["Todos"]
if f_setor1 != "Todos":
    opts_setor2 += sorted(df_seeg[df_seeg['setor_nivel1'] == f_setor1]['setor_nivel2'].dropna().unique())
else:
    opts_setor2 += sorted(df_seeg['setor_nivel2'].dropna().unique())
f_setor2 = st.sidebar.selectbox("Categoria de Emissão", opts_setor2)

opts_setor3 = ["Todos"]
if f_setor2 != "Todos":
    opts_setor3 += sorted(df_seeg[df_seeg['setor_nivel2'] == f_setor2]['setor_nivel3'].dropna().unique())
elif f_setor1 != "Todos":
    opts_setor3 += sorted(df_seeg[df_seeg['setor_nivel1'] == f_setor1]['setor_nivel3'].dropna().unique())
else:
    opts_setor3 += sorted(df_seeg['setor_nivel3'].dropna().unique())
f_setor3 = st.sidebar.selectbox("Subcategoria de Emissão", opts_setor3)

# Função auxiliar para filtrar
def apply_filters(df, has_bioma=True):
    temp = df.copy()
    if 'ano' in temp.columns:
        temp = temp[(temp['ano'] >= f_ano[0]) & (temp['ano'] <= f_ano[1])]
    if f_estado != "Todos" and 'estado' in temp.columns:
        temp = temp[temp['estado'] == f_estado]
    if has_bioma and f_bioma != "Todos":
        if 'bioma' in temp.columns:
            temp = temp[temp['bioma'] == f_bioma]
        elif 'nome_bioma' in temp.columns:
            temp = temp[temp['nome_bioma'] == f_bioma]
    if f_setor1 != "Todos" and 'setor_nivel1' in temp.columns:
        temp = temp[temp['setor_nivel1'] == f_setor1]
    if f_setor2 != "Todos" and 'setor_nivel2' in temp.columns:
        temp = temp[temp['setor_nivel2'] == f_setor2]
    if f_setor3 != "Todos" and 'setor_nivel3' in temp.columns:
        temp = temp[temp['setor_nivel3'] == f_setor3]
    return temp

# Filtrando bases principais
s_seeg = apply_filters(df_seeg)
s_desm = apply_filters(df_desm, has_bioma=False) # silver_desmatamento nem sempre tem bioma direto
s_past = apply_filters(df_past, has_bioma=False)
s_chuva = apply_filters(df_chuva, has_bioma=False)
s_cob = apply_filters(df_cob, has_bioma=False)
s_desm_est = apply_filters(df_desm_est, has_bioma=True)

if len(s_seeg) == 0:
    st.warning("A combinação de filtros não retornou dados para o SEEG. Tente ajustar.")
    st.stop()

# ==============================================================================
# PÁGINA 1: VISÃO EXECUTIVA
# ==============================================================================
if page == "Visão Executiva":
    st.header("Visão Executiva & Scorecard ESG")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Função para formatar os números
    def formatar_numero(valor, unidade=""):
        if valor >= 1e12:
            num = valor / 1e12
            sufixo = "Tri"
        elif valor >= 1e9:
            num = valor / 1e9
            sufixo = "Bi"
        elif valor >= 1e6:
            num = valor / 1e6
            sufixo = "Mi"
        elif valor >= 1e3:
            num = valor / 1e3
            sufixo = "mil"
        else:
            num = valor
            sufixo = ""
        # Remove casas decimais e usa o separador amigável
        return f"{int(num)} {sufixo} {unidade}".strip()
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Total Emissões Líquidas
    tot_emissoes_brutas = s_seeg['emissao_liquida_toneladas'].sum()
    
    # 2. Porcentagem Agro + Uso do Solo
    setores_agro_solo = ['Agropecuária', 'Mudança de Uso da Terra e Floresta']
    emissoes_agro_solo = s_seeg[s_seeg['setor_nivel1'].isin(setores_agro_solo)]['emissao_liquida_toneladas'].sum()
    pct_agro_solo = (emissoes_agro_solo / tot_emissoes_brutas) * 100 if tot_emissoes_brutas > 0 else 0
    
    # 3. Área Desmatada (bruta em hectares)
    tot_desmatamento = s_desm[s_desm['origem_dados'] == 'fato_desmatamento_estado']['area_ha'].sum()
    
    # 4. Oportunidade Créditos (Reais brutos) — Usa somente o último ano para evitar dupla contagem de área
    df_vigor = s_past[s_past['origem_dados'] == 'fato_pastagem_vigor']
    ano_max_vigor = df_vigor['ano'].max() if len(df_vigor) > 0 else 0
    vigor_ultimo_ano = df_vigor[df_vigor['ano'] == ano_max_vigor]
    pastagem_deg = vigor_ultimo_ano[vigor_ultimo_ano['classe_nivel_2'].isin(['Vigor Condition Low', 'Vigor Condition Average'])]['area_ha'].sum()
    receita_carbono = pastagem_deg * 2.0 * 50
    
    col1.metric("Emissões Líquidas", formatar_numero(tot_emissoes_brutas, "tCO₂e"), help="Total de emissões líquidas considerando todos os setores na seleção atual.")
    col2.metric("Agro + Uso do Solo", f"{int(pct_agro_solo)}%", help="Porcentagem total de emissões do setor agropecuário mais Uso de Solos, no qual este está incluso desmatamento e manejos de solo.")
    col3.metric("Área Desmatada", formatar_numero(tot_desmatamento, "ha"), help="Área total desmatada bruta em hectares (inclui sobreposição de alertas dependendo do filtro).")
    col4.metric("Potencial Carbono", f"R$ {formatar_numero(receita_carbono)}", help="Estimativa financeira baseada na precificação da recuperação de hectares de pastagens com vigor baixo/médio.")
    
    # Mais espaço entre os gráficos
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    c1, spacer, c2 = st.columns([1, 0.05, 1])
    
    with c1:
        # Gráfico de Colunas por Setor Geral (Substituindo Waterfall)
        df_cols = s_seeg.groupby('setor_nivel1')['emissao_liquida_toneladas'].sum().reset_index()
        df_cols = df_cols.sort_values(by='emissao_liquida_toneladas', ascending=False)
        fig_cols = px.bar(
            df_cols, 
            x='setor_nivel1', 
            y='emissao_liquida_toneladas',
            title="Emissões Líquidas por Setor Geral",
            labels={'setor_nivel1': 'Setor', 'emissao_liquida_toneladas': 'Emissões (tCO₂e)'}
        )
        fig_cols.update_traces(marker_color='#007A33')
        fig_cols.update_layout(height=450, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', margin=dict(t=40, l=20, r=20, b=20))
        st.plotly_chart(fig_cols, use_container_width=True)

    with c2:
        # Gráfico de Área Empilhada: Evolução Histórica (Movido para cima)
        setores_historico = ['Mudança de Uso da Terra e Floresta', 'Energia', 'Agropecuária']
        df_hist = s_seeg[s_seeg['setor_nivel1'].isin(setores_historico)]
        df_hist_agg = df_hist.groupby(['ano', 'setor_nivel1'])['emissao_liquida_toneladas'].sum().reset_index()
        
        if len(df_hist_agg) > 0:
            fig_area = px.area(
                df_hist_agg,
                x='ano',
                y='emissao_liquida_toneladas',
                color='setor_nivel1',
                title="Evolução das Emissões por Setor Chave",
                labels={'ano': 'Ano', 'emissao_liquida_toneladas': 'Emissões Líquidas', 'setor_nivel1': 'Setor'},
                color_discrete_map={
                    'Mudança de Uso da Terra e Floresta': '#007A33',
                    'Agropecuária': '#F39C12',
                    'Energia': '#2C3E50'
                }
            )
            fig_area.update_layout(
                height=450, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', margin=dict(t=40, l=20, r=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_area, use_container_width=True)

    # --- GRÁFICOS INFERIORES: Subcategoria e Mapa ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    c3, spacer2, c4 = st.columns([1, 0.05, 1])
    
    with c3:
        # Novo gráfico: Emissões por setor_nivel3 (Subcategoria)
        df_sub = s_seeg.groupby('setor_nivel3')['emissao_liquida_toneladas'].sum().reset_index()
        
        # Como pode haver muitas subcategorias, podemos pegar as top 15 para o gráfico não ficar espremido
        df_sub = df_sub.nlargest(15, 'emissao_liquida_toneladas').sort_values(by='emissao_liquida_toneladas', ascending=True)
        
        if len(df_sub) > 0:
            fig_sub = px.bar(
                df_sub,
                x='emissao_liquida_toneladas',
                y='setor_nivel3',
                orientation='h',
                title="Emissões por Subcategoria (Top 15)",
                labels={'emissao_liquida_toneladas': 'Emissões (tCO₂e)', 'setor_nivel3': 'Subcategoria'}
            )
            fig_sub.update_traces(marker_color='#007A33') 
            fig_sub.update_layout(height=450, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', margin=dict(t=40, l=20, r=20, b=20))
            st.plotly_chart(fig_sub, use_container_width=True)
            
    with c4:
        # Mapa Coroplético de Emissões (Movido para baixo)
        df_mapa = s_seeg.groupby('estado')['emissao_liquida_toneladas'].sum().reset_index()
        if len(df_mapa) > 0:
            fig_map = px.choropleth(
                df_mapa,
                geojson=brazil_geojson,
                locations='estado',
                featureidkey="properties.name", 
                color='emissao_liquida_toneladas',
                color_continuous_scale='Reds',
                title="Mapa de Emissões Líquidas por Estado",
                labels={'emissao_liquida_toneladas': 'Emissões (tCO₂e)'}
            )
            fig_map.update_geos(fitbounds="locations", visible=False)
            fig_map.update_layout(
                height=450, margin={"r":0,"t":25,"l":0,"b":0}, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
                coloraxis_colorbar=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_map, use_container_width=True)

# ==============================================================================
# PÁGINA 2: EMISSÕES & CLIMA
# ==============================================================================
elif page == "Emissões & Clima":
    from plotly.subplots import make_subplots
    st.header("Relação de Emissão e Clima na Agropecuária")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. Preparação dos dados para métricas
    import scipy.stats as stats
    
    media_precipitacao = s_chuva['Chuva_mm'].mean() if len(s_chuva) > 0 else 0
    
    # Teste de Hipótese (Pearson) por Estado
    chuva_anual_hp = s_chuva.groupby(['estado', 'ano'])['Chuva_mm'].sum().reset_index()
    emis_anual_hp = s_seeg[s_seeg['setor_nivel1'] == 'Agropecuária'].groupby(['estado', 'ano'])['emissao_liquida_toneladas'].sum().reset_index()
    df_hp_join = pd.merge(chuva_anual_hp, emis_anual_hp, on=['estado', 'ano'], how='inner')
    
    estados_h0_rejeitada = 0
    total_estados_teste = 0
    for est in df_hp_join['estado'].unique():
        df_e = df_hp_join[df_hp_join['estado'] == est]
        if len(df_e) >= 3: # Pearson exige pelo menos 3 pontos
            corr, p_value = stats.pearsonr(df_e['Chuva_mm'], df_e['emissao_liquida_toneladas'])
            if not pd.isna(p_value):
                total_estados_teste += 1
                # O usuário definiu H0: "Estão relacionadas". 
                # Estatisticamente, p < 0.05 prova correlação. Logo, p >= 0.05 rejeita a relação.
                if p_value >= 0.05:
                    estados_h0_rejeitada += 1
                    
    help_hp = (
        "Teste de Correlação de Pearson (α = 5%). O teste mediu a dependência linear entre chuva "
        "anual e emissões agropecuárias por estado. Em estatística, H0 é 'Sem relação'. Como sua "
        "H0 inverteu isso ('Estão relacionadas'), a rejeição da sua H0 ocorre quando o p-valor >= 0.05 "
        "(falta de evidência de correlação). O número mostra quantos estados não apresentaram relação significativa."
    )
    
    df_chuva_estado = s_chuva.groupby('estado')['Chuva_mm'].sum().reset_index()
    if len(df_chuva_estado) > 0:
        estado_mais_chuva = df_chuva_estado.loc[df_chuva_estado['Chuva_mm'].idxmax()]['estado']
        estado_menos_chuva = df_chuva_estado.loc[df_chuva_estado['Chuva_mm'].idxmin()]['estado']
    else:
        estado_mais_chuva = "N/A"
        estado_menos_chuva = "N/A"
        
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Precipitação Média Anual", f"{media_precipitacao:,.1f} mm", help="Média de precipitação anual para o período e região selecionados.")
    col2.metric("Teste Hipótese: H0 Rejeitada", f"{estados_h0_rejeitada} / {total_estados_teste} UFs", help=help_hp)
    col3.metric("Maior Precipitação", estado_mais_chuva, help="Estado com o maior volume acumulado de chuvas no período.")
    col4.metric("Menor Precipitação", estado_menos_chuva, help="Estado com o menor volume acumulado de chuvas no período.")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, spacer, c2 = st.columns([1, 0.05, 1])
    
    with c1:
        chuva_ano = s_chuva.groupby('ano')['Chuva_mm'].mean().reset_index()
        s_seeg_agro = s_seeg[s_seeg['setor_nivel1'] == 'Agropecuária']
        emis_ano = s_seeg_agro.groupby('ano')['emissao_liquida_toneladas'].sum().reset_index()
        df_ano = pd.merge(chuva_ano, emis_ano, on='ano', how='inner')
        
        if len(df_ano) > 0:
            fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
            fig_dual.add_trace(
                go.Bar(x=df_ano['ano'], y=df_ano['Chuva_mm'], name="Chuva Média (mm)", marker_color="#3498DB"),
                secondary_y=False,
            )
            fig_dual.add_trace(
                go.Scatter(x=df_ano['ano'], y=df_ano['emissao_liquida_toneladas'], name="Emissões Líquidas", line=dict(color="#DC2626", width=3)),
                secondary_y=True,
            )
            fig_dual.update_layout(
                title="Chuva Média Anual vs Emissões", paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', margin=dict(t=40, l=20, r=20, b=80), height=400,
                legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_dual, use_container_width=True)
            
    with c2:
        chuva_anual_est = s_chuva.groupby(['estado', 'ano'])['Chuva_mm'].sum().reset_index()
        emis_anual_est = s_seeg[s_seeg['setor_nivel1'] == 'Agropecuária'].groupby(['estado', 'ano'])['emissao_liquida_toneladas'].sum().reset_index()
        df_corr_join = pd.merge(chuva_anual_est, emis_anual_est, on=['estado', 'ano'], how='inner')
        
        corrs = []
        for est in df_corr_join['estado'].unique():
            df_e = df_corr_join[df_corr_join['estado'] == est]
            if len(df_e) >= 3:
                corr, p_value = stats.pearsonr(df_e['Chuva_mm'], df_e['emissao_liquida_toneladas'])
                if not pd.isna(corr) and not pd.isna(p_value):
                    status_h0 = "H0 Rejeitada (Sem Relação)" if p_value >= 0.05 else "H0 Não Rejeitada (Com Relação)"
                    corrs.append({'estado': est, 'Correlacao': corr, 'abs_corr': abs(corr), 'Status': status_h0})
        
        if len(corrs) > 0:
            df_corr = pd.DataFrame(corrs)
            fig_tree = px.treemap(
                df_corr, 
                path=['Status', 'estado'], 
                values='abs_corr', 
                color='Status',
                color_discrete_map={"H0 Rejeitada (Sem Relação)": "#7F8C8D", "H0 Não Rejeitada (Com Relação)": "#007A33"},
                title="Status do Teste de Hipótese por Estado"
            )
            fig_tree.update_traces(textfont=dict(color='white'))
            fig_tree.update_layout(height=400, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', margin=dict(t=40, l=20, r=20, b=20))
            st.plotly_chart(fig_tree, use_container_width=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    c3, spacer2, c4 = st.columns([1, 0.05, 1])
    
    with c3:
        s_seeg_agro_n2 = s_seeg[s_seeg['setor_nivel1'] == 'Agropecuária']
        df_area_agro = s_seeg_agro_n2.groupby(['ano', 'setor_nivel2'])['emissao_liquida_toneladas'].sum().reset_index()
        
        if len(df_area_agro) > 0:
            fig_area_agro = px.area(
                df_area_agro, 
                x='ano', 
                y='emissao_liquida_toneladas', 
                color='setor_nivel2',
                title="Evolução Emissões Agropecuárias (Subsetor)",
                labels={'ano': 'Ano', 'emissao_liquida_toneladas': 'Emissões Líquidas (tCO₂e)', 'setor_nivel2': 'Subsetor'}
            )
            fig_area_agro.update_layout(
                height=400, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', margin=dict(t=40, l=20, r=20, b=80),
                legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_area_agro, use_container_width=True)
        else:
            st.info("Não há dados de emissões para o setor Agropecuária nesta seleção.")

    with c4:
        df_chuva_media = s_chuva.groupby('estado')['Chuva_mm'].mean().reset_index()
        if len(df_chuva_media) > 0:
            fig_map_chuva = px.choropleth(
                df_chuva_media,
                geojson=brazil_geojson,
                locations='estado',
                featureidkey="properties.name",
                color='Chuva_mm',
                color_continuous_scale='Blues',
                title="Mapa: Precipitação Média por Estado",
                labels={'Chuva_mm': 'Precipitação (mm)'}
            )
            fig_map_chuva.update_geos(fitbounds="locations", visible=False)
            fig_map_chuva.update_layout(
                height=400, margin={"r":0,"t":40,"l":0,"b":0}, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
                coloraxis_colorbar=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_map_chuva, use_container_width=True)
        else:
            st.info("Sem dados de chuva para o mapa.")

# ==============================================================================
# PÁGINA 3: USO DA TERRA & RISCO
# ==============================================================================
elif page == "Uso da Terra & Risco":
    st.header("Análise de Uso da Terra e Emissões por Desmatamento")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. Emissões totais por desmatamento
    emis_desm = s_seeg[s_seeg['setor_nivel1'] == 'Mudança de Uso da Terra e Floresta']['emissao_liquida_toneladas'].sum()
    
    # 2 e 3. Variação do tamanho da área da floresta e agropecuária
    ano_min_cob = s_cob['ano'].min() if len(s_cob) > 0 else 0
    ano_max_cob = s_cob['ano'].max() if len(s_cob) > 0 else 0
    
    # Usando str.contains para evitar problemas com números no início do nome da classe
    flor_mask = s_cob['classe_nivel_1'].str.contains('Floresta', case=False, na=False)
    agro_mask = s_cob['classe_nivel_1'].str.contains('Agropecu', case=False, na=False)
    
    area_flor_min = s_cob[(s_cob['ano'] == ano_min_cob) & flor_mask]['area_ha'].sum()
    area_flor_max = s_cob[(s_cob['ano'] == ano_max_cob) & flor_mask]['area_ha'].sum()
    var_flor = area_flor_max - area_flor_min
    pct_flor = (var_flor / area_flor_min * 100) if area_flor_min > 0 else 0

    area_agro_min = s_cob[(s_cob['ano'] == ano_min_cob) & agro_mask]['area_ha'].sum()
    area_agro_max = s_cob[(s_cob['ano'] == ano_max_cob) & agro_mask]['area_ha'].sum()
    var_agro = area_agro_max - area_agro_min
    pct_agro = (var_agro / area_agro_min * 100) if area_agro_min > 0 else 0

    # 4. Área total desmatada em terras indígenas e unidades de conservação
    area_desm_ti_uc = s_desm[s_desm['origem_dados'].isin(['fato_desmatamento_terra_indigena', 'fato_desmatamento_unidade_conservacao'])]['area_ha'].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Emissões por Desmatamento", f"{emis_desm/1e9:,.1f} Bi tCO₂e", help="Total de emissões da classe Mudança de Uso da Terra e Floresta no período selecionado.")
    col2.metric("Variação Área Floresta", f"{area_flor_max/1e6:,.2f} Mi ha", delta=f"{pct_flor:+.2f}%", help=f"Tamanho da área de Floresta em {ano_max_cob} comparado com {ano_min_cob}.")
    col3.metric("Variação Área Agropecuária", f"{area_agro_max/1e6:,.2f} Mi ha", delta=f"{pct_agro:+.2f}%", delta_color="inverse", help=f"Tamanho da área Agropecuária (Pastagem+Agricultura) em {ano_max_cob} comparado com {ano_min_cob}. (Crescimento é marcado vermelho no contexto de desmatamento)")
    col4.metric("Desmatamento TI / UC", f"{area_desm_ti_uc/1000:,.1f} mil ha", help="Soma total da área desmatada em Terras Indígenas e Unidades de Conservação.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, spacer, c2 = st.columns([1, 0.05, 1])
    
    with c1:
        # Gráfico Comparativo: Ano Inicial vs Ano Final
        df_comp = s_cob[(s_cob['ano'] == ano_min_cob) | (s_cob['ano'] == ano_max_cob)].copy()
        
        # Filtrar apenas Floresta e Agropecuária
        df_comp = df_comp[df_comp['classe_nivel_1'].str.contains('Floresta|Agropecu', case=False, na=False)]
        
        # Limpar o nome da classe
        df_comp['Classe'] = df_comp['classe_nivel_1'].apply(lambda x: "Floresta" if "Floresta" in str(x) else "Agropecuária")
        
        df_comp_agg = df_comp.groupby(['ano', 'Classe'])['area_ha'].sum().reset_index()
        df_comp_agg['area_ha'] = df_comp_agg['area_ha'] / 1e6
        df_comp_agg['ano'] = df_comp_agg['ano'].astype(str) # Para usar eixo categórico
        
        if len(df_comp_agg) > 0:
            fig_bar_comp = px.bar(
                df_comp_agg, 
                x='Classe', 
                y='area_ha', 
                color='ano', 
                barmode='group',
                title=f"Variação: {ano_min_cob} vs {ano_max_cob} (Milhões ha)", 
                color_discrete_sequence=["#95A5A6", "#E74C3C"], # Cinza para ano inicial, Vermelho para final
                labels={'Classe': 'Uso do Solo', 'area_ha': 'Área (Mi ha)', 'ano': 'Ano'}
            )
            fig_bar_comp.update_layout(height=400, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', margin=dict(t=40, l=20, r=20, b=20))
            st.plotly_chart(fig_bar_comp, use_container_width=True)
            
    with c2:
        # Alarme EUDR - Agora em Gráfico de Área
        df_eudr = s_desm[s_desm['origem_dados'].isin(['fato_desmatamento_terra_indigena', 'fato_desmatamento_unidade_conservacao'])]
        if len(df_eudr) > 0:
            df_eudr_agg = df_eudr.groupby(['ano', 'origem_dados'])['area_ha'].sum().reset_index()
            map_origem = {
                'fato_desmatamento_terra_indigena': 'Terra Indígena',
                'fato_desmatamento_unidade_conservacao': 'Unidade de Conservação'
            }
            df_eudr_agg['origem_dados'] = df_eudr_agg['origem_dados'].map(map_origem).fillna(df_eudr_agg['origem_dados'])
            
            fig_eudr = px.area(
                df_eudr_agg, 
                x='ano', 
                y='area_ha', 
                color='origem_dados', 
                title="Alerta EUDR: Desmatamento em Áreas Protegidas",
                labels={'ano': 'Ano', 'area_ha': 'Área Desmatada (ha)', 'origem_dados': 'Local'}
            )
            fig_eudr.update_layout(height=400, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', margin=dict(t=40, l=20, r=20, b=20))
            st.plotly_chart(fig_eudr, use_container_width=True)
        else:
            st.success("Zero desmatamento em TI/UC para esta seleção.")

# ==============================================================================
# PÁGINA 4: PASTAGENS E CARBONO
# ==============================================================================
elif page == "Pastagens & Carbono":
    st.header("Mercado de Carbono e Recuperação de Pastagens")
    st.markdown("<br>", unsafe_allow_html=True)
    
    df_vigor = s_past[s_past['origem_dados'] == 'fato_pastagem_vigor']
    if len(df_vigor) > 0:
        ano_max = df_vigor['ano'].max()
        vigor_recente = df_vigor[df_vigor['ano'] == ano_max]
        
        area_saudavel = vigor_recente[vigor_recente['classe_nivel_2'] == 'Vigor Condition High']['area_ha'].sum()
        area_degradada = vigor_recente[vigor_recente['classe_nivel_2'].isin(['Vigor Condition Low', 'Vigor Condition Average'])]['area_ha'].sum()
        
        # 1. Potencial Sequestro
        potencial_tco2e = area_degradada * 2.0
        
        # 2. Receitas
        receita_min = potencial_tco2e * 25
        receita_base = potencial_tco2e * 50
        receita_max = potencial_tco2e * 150
        
        # 3. ROI (Assumindo R$ 50/ha para custo MRV baseado em estimativas conservadoras)
        custo_mrv_total = area_degradada * 50
        roi = ((receita_base - custo_mrv_total) / custo_mrv_total * 100) if custo_mrv_total > 0 else 0
        
        # 4. Taxa de Conversão
        ano_min_cob = s_cob['ano'].min() if len(s_cob) > 0 else 0
        # Layout dos Cartões
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Área Pastagem Saudável", f"{area_saudavel/1e6:,.2f} Mi ha", help="Área classificada como Vigor Condition High.")
        col2.metric("Área Pastagem Degradada", f"{area_degradada/1e6:,.2f} Mi ha", help="Área classificada como Vigor Condition Low ou Average.")
        col3.metric("Potencial Sequestro tCO₂e", f"{potencial_tco2e/1e6:,.2f} Mi t", help="Estimativa conservadora: 2 tCO₂e sequestradas por hectare de pastagem degradada recuperada.")
        
        help_receita = f"Receita Base: R$ 50/tCO₂e.\nCenário Mínimo (R$ 25/t): R$ {receita_min/1e9:,.2f} Bi\nCenário Máximo (R$ 150/t): R$ {receita_max/1e9:,.2f} Bi"
        col4.metric("Receita de Carbono (Base)", f"R$ {receita_base/1e9:,.2f} Bi", help=help_receita)

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Preparação de Dados por Estado
        df_vigor_estado = vigor_recente.groupby(['estado', 'classe_nivel_2'])['area_ha'].sum().reset_index()
        df_vigor_pivot = df_vigor_estado.pivot(index='estado', columns='classe_nivel_2', values='area_ha').fillna(0)
        for col in ['Vigor Condition High', 'Vigor Condition Average', 'Vigor Condition Low']:
            if col not in df_vigor_pivot.columns:
                df_vigor_pivot[col] = 0
                
        df_vigor_pivot['Area_Degradada'] = df_vigor_pivot['Vigor Condition Average'] + df_vigor_pivot['Vigor Condition Low']
        df_vigor_pivot['Total'] = df_vigor_pivot['Vigor Condition High'] + df_vigor_pivot['Area_Degradada']
        df_vigor_pivot['Pct_Degradada'] = (df_vigor_pivot['Area_Degradada'] / df_vigor_pivot['Total']) * 100
        df_vigor_pivot['Potencial_Receita_Base_R$'] = df_vigor_pivot['Area_Degradada'] * 2.0 * 50
        df_vigor_pivot = df_vigor_pivot.reset_index()
        
        c1, spacer, c2 = st.columns([1, 0.05, 1])
        with c1:
            if len(df_vigor_pivot) > 0:
                fig_map_deg = px.choropleth(
                    df_vigor_pivot,
                    geojson=brazil_geojson,
                    locations='estado',
                    featureidkey="properties.name",
                    color='Pct_Degradada',
                    color_continuous_scale='YlOrRd',
                    hover_data={'Potencial_Receita_Base_R$': ':,.2f', 'estado': False},
                    title="Concentração de Pastagens Degradadas",
                    labels={'Pct_Degradada': '% Degradada', 'Potencial_Receita_Base_R$': 'Receita (R$)'}
                )
                fig_map_deg.update_geos(fitbounds="locations", visible=False)
                fig_map_deg.update_layout(
                    height=450, margin={"r":0,"t":40,"l":0,"b":0}, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
                    coloraxis_colorbar=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_map_deg, use_container_width=True)
                
        with c2:
            emis_agro_estado = s_seeg[(s_seeg['setor_nivel1'] == 'Agropecuária') & (s_seeg['ano'] == ano_max)].groupby('estado')['emissao_liquida_toneladas'].sum().reset_index()
            df_scatter = pd.merge(df_vigor_pivot, emis_agro_estado, on='estado', how='inner')
            if len(df_scatter) > 0:
                # Quadrante superior direito = Alta emissão, Alta degradação
                fig_scatter = px.scatter(
                    df_scatter,
                    x='emissao_liquida_toneladas',
                    y='Area_Degradada',
                    text='estado',
                    size='Potencial_Receita_Base_R$',
                    color='Pct_Degradada',
                    color_continuous_scale='YlOrRd',
                    title="Prioridade Geográfica para Projetos Piloto",
                    labels={'emissao_liquida_toneladas': 'Emissões Agropecuárias (tCO₂e)', 'Area_Degradada': 'Área Degradada (ha)'}
                )
                fig_scatter.update_traces(textposition='top center')
                fig_scatter.update_layout(height=450, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', margin=dict(t=40, l=20, r=20, b=20))
                st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Intensidade de Carbono sobre Pastagem
        # Usamos s_past em vez de s_cob pois a base de cobertura nível 1 agregada nacionalmente não possui campo "estado"
        # Excluímos emissões de "Cultivo em sistema irrigado inundado" (arroz) pois não correspondem à área de pastagem
        emis_agro_sem_arroz = s_seeg[
            (s_seeg['setor_nivel1'] == 'Agropecuária') & 
            (s_seeg['ano'] == ano_max) & 
            (s_seeg['setor_nivel3'] != 'Cultivo em sistema irrigado inundado')
        ].groupby('estado')['emissao_liquida_toneladas'].sum().reset_index()
        past_estado = s_past[s_past['ano'] == ano_max].groupby('estado')['area_ha'].sum().reset_index()
        past_estado.rename(columns={'area_ha': 'area_pastagem_total'}, inplace=True)
        df_int = pd.merge(emis_agro_sem_arroz, past_estado, on='estado', how='inner')
        if len(df_int) > 0:
            df_int['Intensidade_Carbono'] = df_int['emissao_liquida_toneladas'] / df_int['area_pastagem_total']
            df_int = df_int.sort_values('Intensidade_Carbono', ascending=False)
            
            fig_int = px.bar(
                df_int,
                x='estado',
                y='Intensidade_Carbono',
                title="Intensidade de Carbono por Hectare Agropecuário",
                labels={'estado': 'Estado', 'Intensidade_Carbono': 'tCO₂e / ha'}
            )
            fig_int.update_traces(marker_color='#1B4332')
            fig_int.update_layout(height=400, paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', margin=dict(t=40, l=20, r=20, b=20))
            st.plotly_chart(fig_int, use_container_width=True)
            
    else:
        st.info("Sem dados de pastagem para esta seleção.")


