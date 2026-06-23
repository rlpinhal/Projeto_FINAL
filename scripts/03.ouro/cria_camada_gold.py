# ============================================================
# SCRIPT: Silver -> Gold -- Criacao do Star Schema ESG
# ============================================================
import pandas as pd
import numpy as np
import os
import sys
import warnings
warnings.filterwarnings('ignore')

sys.stdout.reconfigure(encoding='utf-8')

print("Iniciando construcao da Camada Gold (Star Schema)...\n")

DIR_SILVER_SEEG = os.path.join("dados", "02.silver", "SEEG")
DIR_SILVER_MAPBIOMAS = os.path.join("dados", "02.silver", "mapbiomas")
DIR_SILVER_NASA = os.path.join("dados", "02.silver", "nasa")
DIR_SILVER_CROP = os.path.join("dados", "02.silver", "crop_yieldKAGGLE.csv")

DIR_GOLD = os.path.join("dados", "03.gold", "star_schema")
os.makedirs(DIR_GOLD, exist_ok=True)

# Dicionario para uniformizar nomes de estados e regioes
mapa_estados_regioes = {
    'Acre': ('AC', 'Norte'), 'Alagoas': ('AL', 'Nordeste'), 'Amapá': ('AP', 'Norte'),
    'Amazonas': ('AM', 'Norte'), 'Bahia': ('BA', 'Nordeste'), 'Ceará': ('CE', 'Nordeste'),
    'Distrito Federal': ('DF', 'Centro-Oeste'), 'Espírito Santo': ('ES', 'Sudeste'),
    'Goiás': ('GO', 'Centro-Oeste'), 'Maranhão': ('MA', 'Nordeste'), 'Mato Grosso': ('MT', 'Centro-Oeste'),
    'Mato Grosso Do Sul': ('MS', 'Centro-Oeste'), 'Minas Gerais': ('MG', 'Sudeste'),
    'Pará': ('PA', 'Norte'), 'Paraíba': ('PB', 'Nordeste'), 'Paraná': ('PR', 'Sul'),
    'Pernambuco': ('PE', 'Nordeste'), 'Piauí': ('PI', 'Nordeste'), 'Rio De Janeiro': ('RJ', 'Sudeste'),
    'Rio Grande Do Norte': ('RN', 'Nordeste'), 'Rio Grande Do Sul': ('RS', 'Sul'),
    'Rondônia': ('RO', 'Norte'), 'Roraima': ('RR', 'Norte'), 'Santa Catarina': ('SC', 'Sul'),
    'São Paulo': ('SP', 'Sudeste'), 'Sergipe': ('SE', 'Nordeste'), 'Tocantins': ('TO', 'Norte')
}

mapa_sigla_estado = {sigla: est for est, (sigla, reg) in mapa_estados_regioes.items()}

def padronizar_estado(val, sigla=False):
    if pd.isna(val): return np.nan
    val_str = str(val).strip().title()
    if sigla and val_str.upper() in mapa_sigla_estado:
        return mapa_sigla_estado[val_str.upper()]
    return val_str

# ============================================================
# 1. PROCESSAMENTO DE TABELAS FATO
# ============================================================

# 1.1 FATO EMISSÕES (SEEG)
print("Processando Fato Emissões (SEEG)...")
df_fato_emissoes = pd.DataFrame()
try:
    df_seeg = pd.read_csv(os.path.join(DIR_SILVER_SEEG, "silver_seeg_all.csv"), low_memory=False)
    # Filtrar apenas Agropecuaria para simplificar, ou manter tudo. Vamos manter Agropecuaria.
    df_seeg_agro = df_seeg[df_seeg['setor_nivel1'] == 'Agropecuária']
    df_seeg_agro['estado'] = df_seeg_agro['estado'].apply(lambda x: padronizar_estado(x))
    df_seeg_agro['bioma'] = df_seeg_agro['bioma'].str.title()
    df_fato_emissoes = df_seeg_agro.groupby(['ano', 'estado', 'bioma', 'setor_nivel2'])['emissao_liquida_toneladas'].sum().reset_index()
    df_fato_emissoes.rename(columns={'emissao_liquida_toneladas': 'emissao_agro_tco2e'}, inplace=True)
except Exception as e:
    print(f"  ⚠️ Erro SEEG: {e}")

# 1.2 FATO CLIMA (NASA)
print("Processando Fato Clima (NASA)...")
df_fato_clima = pd.DataFrame()
try:
    df_clima = pd.read_csv(os.path.join(DIR_SILVER_NASA, "silver_nasa_chuva_estados_brasil.csv"), sep=';')
    # Tem 'UF', 'Ano', 'Mes', 'Chuva_mm'
    df_clima['estado'] = df_clima['UF'].apply(lambda x: padronizar_estado(x, sigla=True))
    df_clima.rename(columns={'Ano': 'ano', 'Mes': 'mes', 'Chuva_mm': 'chuva_mm'}, inplace=True)
    df_fato_clima = df_clima[['ano', 'mes', 'estado', 'chuva_mm']]
except Exception as e:
    print(f"  ⚠️ Erro Clima: {e}")

# 1.3 FATO PASTAGEM
print("Processando Fato Pastagem...")
df_fato_pastagem = pd.DataFrame()
try:
    df_past = pd.read_csv(os.path.join(DIR_SILVER_MAPBIOMAS, "silver_pastagem.csv"))
    df_past['estado'] = df_past['nome_estado'].apply(lambda x: padronizar_estado(x))
    df_past['bioma'] = df_past['nome_bioma'].str.title()
    
    # Degradação (Vigor)
    df_vigor = df_past[df_past['origem_dados'] == 'fato_pastagem_vigor']
    df_vigor_deg = df_vigor[df_vigor['classe_nivel_2'].isin(['Vigor Condition Low', 'Vigor Condition Average'])]
    df_vigor_agg = df_vigor_deg.groupby(['ano', 'estado', 'bioma'])['area_ha'].sum().reset_index()
    df_vigor_agg.rename(columns={'area_ha': 'area_pastagem_degradada_ha'}, inplace=True)
    
    # Idade Media
    df_idade = df_past[df_past['origem_dados'] == 'fato_pastagem_idade']
    df_idade['idade_x_area'] = df_idade['idade_pastagem_anos'] * df_idade['area_ha']
    df_idade_agg = df_idade.groupby(['ano', 'estado', 'bioma']).agg({'idade_x_area': 'sum', 'area_ha': 'sum'}).reset_index()
    df_idade_agg['idade_media_pastagem'] = df_idade_agg['idade_x_area'] / df_idade_agg['area_ha']
    df_idade_agg.drop(columns=['idade_x_area', 'area_ha'], inplace=True)
    
    df_fato_pastagem = pd.merge(df_vigor_agg, df_idade_agg, on=['ano', 'estado', 'bioma'], how='outer')
except Exception as e:
    print(f"  ⚠️ Erro Pastagem: {e}")

# 1.4 FATO DESMATAMENTO
print("Processando Fato Desmatamento...")
df_fato_desmatamento = pd.DataFrame()
try:
    df_desm = pd.read_csv(os.path.join(DIR_SILVER_MAPBIOMAS, "silver_desmatamento.csv"))
    df_desm['bioma'] = df_desm['nome_bioma'].str.title()
    df_desm['regiao'] = df_desm['nome_regiao'].str.title()
    
    # Agrupar por tipo_recorte (origem_dados)
    # fato_desmatamento_terra_indigena, unidade_conservacao, bacia, estado
    
    # Mapear origem_dados para um tipo amigavel
    mapa_recorte = {
        'fato_desmatamento_estado': 'Total Estado',
        'fato_desmatamento_terra_indigena': 'Terra Indigena',
        'fato_desmatamento_unidade_conservacao': 'Unidade de Conservacao',
        'fato_desmatamento_bacia': 'Bacia Hidrografica'
    }
    df_desm['tipo_recorte'] = df_desm['origem_dados'].map(mapa_recorte)
    
    if 'nome_estado' in df_desm.columns:
        df_desm['estado'] = df_desm['nome_estado'].apply(lambda x: padronizar_estado(x))
    else:
        df_desm['estado'] = np.nan
        
    df_fato_desmatamento = df_desm.groupby(['ano', 'estado', 'bioma', 'regiao', 'tipo_recorte'])['area_ha'].sum().reset_index()
    df_fato_desmatamento.rename(columns={'area_ha': 'area_desmatada_ha'}, inplace=True)
except Exception as e:
    print(f"  ⚠️ Erro Desmatamento: {e}")

# 1.5 FATO PRODUTIVIDADE (Crop Yield)
print("Processando Fato Produtividade...")
df_fato_produtividade = pd.DataFrame()
try:
    df_crop = pd.read_csv(os.path.join(DIR_SILVER_CROP, "crop_yield_silver.csv"))
    df_crop['regiao'] = df_crop['regiao'].str.title()
    df_fato_produtividade = df_crop.copy()
except Exception as e:
    print(f"  ⚠️ Erro Produtividade: {e}")


# ============================================================
# 2. CONSTRUÇÃO DAS DIMENSÕES
# ============================================================
print("\nConstruindo Tabelas Dimensão...")

# Dimensão Estado/Região
# Vamos usar o nosso dicionario `mapa_estados_regioes` para gerar uma dimensao fixa e limpa
dados_estado = []
for est, (sigla, reg) in mapa_estados_regioes.items():
    dados_estado.append({'estado': est, 'sigla_estado': sigla, 'regiao': reg})
df_dim_estado = pd.DataFrame(dados_estado)

# Dimensão Bioma
# Coletar biomas unicos das tabelas
biomas = set()
for df in [df_fato_emissoes, df_fato_pastagem, df_fato_desmatamento]:
    if not df.empty and 'bioma' in df.columns:
        biomas.update(df['bioma'].dropna().unique())
df_dim_bioma = pd.DataFrame({'bioma': list(biomas)})

# Dimensão Calendário (Ano)
anos = set()
for df in [df_fato_emissoes, df_fato_pastagem, df_fato_desmatamento, df_fato_clima]:
    if not df.empty and 'ano' in df.columns:
        anos.update(df['ano'].dropna().unique())
df_dim_calendario = pd.DataFrame({'ano': sorted(list(anos))})


# ============================================================
# 3. EXPORTAÇÃO
# ============================================================
print("\nSalvando Star Schema...")

tabelas = {
    'dim_estado.csv': df_dim_estado,
    'dim_bioma.csv': df_dim_bioma,
    'dim_calendario.csv': df_dim_calendario,
    'fato_emissoes.csv': df_fato_emissoes,
    'fato_clima.csv': df_fato_clima,
    'fato_pastagem.csv': df_fato_pastagem,
    'fato_desmatamento.csv': df_fato_desmatamento,
    'fato_produtividade_agricola.csv': df_fato_produtividade
}

for nome_arq, df in tabelas.items():
    if not df.empty:
        caminho = os.path.join(DIR_GOLD, nome_arq)
        df.to_csv(caminho, index=False, encoding='utf-8-sig')
        print(f"   Salvo: {nome_arq} ({df.shape[0]} linhas)")

print("\n✅ Star Schema criado com sucesso! Importe as tabelas no Power BI e relacione os campos 'estado', 'bioma', 'regiao' e 'ano'.")
