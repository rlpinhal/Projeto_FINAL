# ============================================================
# SCRIPT: Bronze -> Silver -- SEEG Raw All (seeg_all.csv)
# ============================================================
# Projeto: Inteligencia Agroambiental -- Creditos de Carbono ESG
# Fonte: SEEG Collection 13 (Sistema de Estimativas de Emissoes e Remocoes de GEE)
# Arquivo: dados/00.raw/seeg_all.csv (332.296 linhas x 46 colunas)
# Data: Junho/2026
#
# Descricao:
#   Replica em Python a transformacao SQL feita no BigQuery:
#   1. UNPIVOT: Formato wide (46 colunas) -> long (1 linha por combinacao)
#   2. Limpeza e tipagem
#   3. Remocao de setor_nivel4 e setor_nivel5 + agregacao (soma emissoes)
#   4. Calculo de emissao liquida (remocoes ficam negativas)
#   5. Filtro: anos >= 2000, sem nulos em emissao/estado
#
# NOTA: setor_nivel4 (Produto_ou_sistema, 174 valores) e setor_nivel5
#       (Detalhamento, 484 valores) foram removidos e as emissoes
#       agregadas por soma. Isso reduz de ~8.3M para ~1.6M linhas (81%).
#
# Entrada:  dados/00.raw/seeg_all.csv
# Saida:    dados/02.silver/SEEG/silver_seeg_all.csv
# ============================================================

# ============================================================
# CELULA 1 -- IMPORTACAO DE BIBLIOTECAS
# ============================================================
# Bibliotecas necessarias para o processamento.
# No Google Colab, todas ja vem instaladas por padrao.

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime

# Configuracoes de exibicao do pandas
pd.set_option('display.max_columns', 20)
pd.set_option('display.max_rows', 30)
pd.set_option('display.float_format', '{:.4f}'.format)

print("Bibliotecas carregadas com sucesso!")
print(f"pandas: {pd.__version__}")
print(f"numpy: {np.__version__}")

# ============================================================
# CELULA 2 -- CONFIGURACOES DO PROJETO
# ============================================================
# Defina os caminhos e parametros aqui.
# Se estiver no Colab, ajuste o CAMINHO_BRONZE para onde fez upload.

# --- Caminhos ---
CAMINHO_BRONZE = os.path.join("dados", "00.raw", "seeg_all.csv")
CAMINHO_SILVER_DIR = os.path.join("dados", "02.silver", "SEEG")
CAMINHO_SILVER_CSV = os.path.join(CAMINHO_SILVER_DIR, "silver_seeg_all.csv")

# --- Parametros ---
PERIODO_INICIO = 2000    # Ano inicial (SQL usava 1990, mas queremos a partir de 2000)
PERIODO_FIM = 2024       # Ano final (ultimo disponivel no arquivo)
CAMADA = "SILVER"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# --- Garantir que a pasta de destino existe ---
os.makedirs(CAMINHO_SILVER_DIR, exist_ok=True)

print(f"\nConfiguracoes:")
print(f"  Arquivo de entrada: {CAMINHO_BRONZE}")
print(f"  Arquivo de saida:   {CAMINHO_SILVER_CSV}")
print(f"  Periodo:            {PERIODO_INICIO}-{PERIODO_FIM}")

# ============================================================
# CELULA 3 -- CARREGAR BRONZE (leitura fiel do arquivo original)
# ============================================================
# Carregamos o CSV exatamente como veio da fonte.
# O arquivo tem 332.296 linhas e 46 colunas:
#   - 11 colunas de metadados (texto)
#   - 35 colunas de anos (1990 a 2024), com prefixo "ano_"
#
# NOTA: O arquivo tem ~152 MB. No Colab, pode levar 15-30 segundos.

print("\n" + "=" * 60)
print("PASSO 1: Carregando arquivo bronze...")
print("=" * 60)

df_bronze = pd.read_csv(
    CAMINHO_BRONZE,
    encoding='utf-8',
    low_memory=False    # Evita warnings de tipos mistos
)

print(f"  Arquivo carregado: {df_bronze.shape[0]:,} linhas x {df_bronze.shape[1]} colunas")
print(f"  Memoria: {df_bronze.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

# Inspecao rapida
print(f"\n  Colunas de metadados:")
colunas_meta = [c for c in df_bronze.columns if not c.startswith('ano_')]
for c in colunas_meta:
    n_unique = df_bronze[c].nunique()
    n_null = df_bronze[c].isnull().sum()
    print(f"    {c}: {n_unique} valores unicos, {n_null:,} nulos")

colunas_anos = [c for c in df_bronze.columns if c.startswith('ano_')]
print(f"\n  Colunas de anos ({len(colunas_anos)}): {colunas_anos[0]} ... {colunas_anos[-1]}")

# ============================================================
# CELULA 4 -- ETAPA 1: UNPIVOT (formato Wide -> Long)
# ============================================================
# Equivalente ao UNPIVOT do BigQuery.
# As 35 colunas de anos (ano_1990 a ano_2024) viram LINHAS.
#
# ANTES (wide):
#   Estado | Setor         | ano_2000 | ano_2001 | ...
#   Acre   | Agropecuaria  | 0.0      | 1.5      | ...
#
# DEPOIS (long):
#   Estado | Setor         | ano_col  | emissao
#   Acre   | Agropecuaria  | ano_2000 | 0.0
#   Acre   | Agropecuaria  | ano_2001 | 1.5
#
# No pandas, isso e feito com pd.melt() -- equivalente ao UNPIVOT do SQL.

print("\n" + "=" * 60)
print("PASSO 2: UNPIVOT -- Convertendo formato Wide para Long...")
print("=" * 60)

# Filtrar apenas colunas de anos >= 2000 ANTES do melt (mais eficiente)
colunas_anos_filtradas = [
    c for c in colunas_anos
    if int(re.search(r'\d{4}', c).group()) >= PERIODO_INICIO
]
print(f"  Colunas de anos selecionadas ({len(colunas_anos_filtradas)}): "
      f"{colunas_anos_filtradas[0]} ... {colunas_anos_filtradas[-1]}")

df_long = pd.melt(
    df_bronze,
    id_vars=colunas_meta,           # Colunas que ficam fixas (metadados)
    value_vars=colunas_anos_filtradas,  # Colunas que viram linhas (anos)
    var_name='ano_col',              # Nome da coluna com o rotulo do ano
    value_name='emissao'             # Nome da coluna com o valor
)

print(f"\n  Resultado do melt:")
print(f"    Antes:  {df_bronze.shape[0]:,} linhas x {df_bronze.shape[1]} colunas")
print(f"    Depois: {df_long.shape[0]:,} linhas x {df_long.shape[1]} colunas")

# Liberar memoria do DataFrame bronze (nao precisamos mais dele)
del df_bronze

# ============================================================
# CELULA 5 -- ETAPA 2: Limpeza, tipagem e padronizacao
# ============================================================
# Equivalente ao bloco SELECT do SQL.
# Aqui transformamos cada coluna para seu formato ideal.

print("\n" + "=" * 60)
print("PASSO 3: Limpeza, tipagem e padronizacao...")
print("=" * 60)

# --- 3.1: Extrair o ano numerico da coluna 'ano_col' ---
# "ano_2000" -> 2000, "ano_2023" -> 2023
# Equivalente SQL: CAST(REGEXP_REPLACE(CAST(ano_col AS STRING), r'[^0-9]', '') AS INT64)
df_long['ano'] = df_long['ano_col'].str.extract(r'(\d{4})').astype(int)
print(f"  [ano] Extraido de 'ano_col': {df_long['ano'].min()} a {df_long['ano'].max()}")

# Remover a coluna intermediaria 'ano_col' (ja extraimos o ano)
df_long = df_long.drop(columns=['ano_col'])

# --- 3.2: Limpar colunas de texto (TRIM + tratar vazios) ---
# Equivalente SQL: TRIM(Estado), NULLIF(TRIM(Bioma), ''), etc.

# Definir quais colunas recebem TRIM
colunas_texto = [
    'Emissao_Remocao_Bunker', 'Gas', 'Setor_de_emissao',
    'Categoria_emissora', 'Sub_categoria_emissora',
    'Recorte', 'Atividade_geral', 'Estado', 'Bioma'
]

for col in colunas_texto:
    if col in df_long.columns:
        # TRIM: remover espacos no inicio e fim
        df_long[col] = df_long[col].astype(str).str.strip()
        # NULLIF: converter strings vazias e 'nan' para None (NaN)
        df_long[col] = df_long[col].replace({'': None, 'nan': None, 'None': None})

print(f"  [texto] TRIM e NULLIF aplicados em {len(colunas_texto)} colunas")

# --- 3.3: Renomear colunas para snake_case padronizado ---
# Equivalente ao aliasing do SQL (AS setor_nivel1, AS tipo_emissao, etc.)
mapa_renomear = {
    'Emissao_Remocao_Bunker': 'tipo_emissao',      # "Emissao" / "Remocao" / "Bunker"
    'Gas': 'gas',
    'Setor_de_emissao': 'setor_nivel1',             # Hierarquia IPCC nivel 1
    'Categoria_emissora': 'setor_nivel2',            # Hierarquia IPCC nivel 2
    'Sub_categoria_emissora': 'setor_nivel3',        # Hierarquia IPCC nivel 3
    'Atividade_geral': 'atividade_geral',
    'Recorte': 'recorte',
    'Estado': 'estado',
    'Bioma': 'bioma',
}

df_long = df_long.rename(columns=mapa_renomear)
print(f"  [renomear] Colunas renomeadas para snake_case")

# --- 3.4: Remover setor_nivel4 e setor_nivel5 (Produto_ou_sistema e Detalhamento) ---
# Essas colunas criam granularidade excessiva (174 e 484 valores unicos).
# Ao remove-las, podemos agregar as emissoes e reduzir ~81% das linhas.
colunas_remover = ['Produto_ou_sistema', 'Detalhamento']
colunas_existentes = [c for c in colunas_remover if c in df_long.columns]
if colunas_existentes:
    df_long = df_long.drop(columns=colunas_existentes)
    print(f"  [remover] Colunas removidas: {colunas_existentes}")

# --- 3.5: Converter emissao para float e tratar nulos ---
# Equivalente SQL: CAST(emissao AS FLOAT64)
df_long['emissao'] = pd.to_numeric(df_long['emissao'], errors='coerce')
print(f"  [emissao] Convertida para float64 ({df_long['emissao'].isnull().sum():,} nulos)")

# Renomear para nome final
df_long = df_long.rename(columns={'emissao': 'emissao_toneladas'})

# ============================================================
# CELULA 6 -- ETAPA 2b: Agregacao (soma das emissoes por grupo)
# ============================================================
# Sem setor_nivel4 e setor_nivel5, existem linhas que agora
# compartilham a mesma combinacao de chaves. Precisamos somar
# as emissoes para nao perder dados.
#
# Exemplo: "Gado de Corte" e "Gado de Leite" (nivel4) sob
# "Fermentacao enterica bovinos" (nivel3) serao somados.

print("\n" + "=" * 60)
print("PASSO 4: Agregando emissoes (soma por grupo sem nivel4/5)...")
print("=" * 60)

linhas_antes_agg = len(df_long)

# Definir colunas de agrupamento (todas as categoricas restantes)
colunas_grupo = [
    'ano', 'estado', 'bioma', 'setor_nivel1', 'setor_nivel2',
    'setor_nivel3', 'atividade_geral', 'recorte', 'tipo_emissao', 'gas'
]

# Agregar: somar emissoes por grupo
df_long = df_long.groupby(
    colunas_grupo, dropna=False
).agg(
    emissao_toneladas=('emissao_toneladas', 'sum')
).reset_index()

linhas_depois_agg = len(df_long)
reducao = (1 - linhas_depois_agg / linhas_antes_agg) * 100
print(f"  Linhas antes:  {linhas_antes_agg:,}")
print(f"  Linhas depois: {linhas_depois_agg:,}")
print(f"  Reducao: {reducao:.1f}% ({linhas_antes_agg - linhas_depois_agg:,} linhas removidas)")

# ============================================================
# CELULA 7 -- ETAPA 2c: Calculo da emissao liquida
# ============================================================
# Equivalente SQL:
#   CASE WHEN LOWER(TRIM(Emissao_Remocao_Bunker)) LIKE '%remo%'
#        THEN -1 * ABS(CAST(emissao AS FLOAT64))
#        ELSE CAST(emissao AS FLOAT64)
#   END AS emissao_liquida_toneladas
#
# Logica: Remocoes (sequestro de carbono) ficam com sinal NEGATIVO.
# Isso permite somar emissoes + remocoes para obter o saldo liquido.

print("\n" + "=" * 60)
print("PASSO 4: Calculando emissao liquida...")
print("=" * 60)

# Identificar linhas de remocao (tipo_emissao contem "remo")
mascara_remocao = df_long['tipo_emissao'].str.lower().str.contains('remo', na=False)

# Calcular emissao liquida:
#   - Remocoes: valor negativo (sequestro)
#   - Emissoes/Bunker: valor positivo (poluicao)
df_long['emissao_liquida_toneladas'] = df_long['emissao_toneladas'].copy()
df_long.loc[mascara_remocao, 'emissao_liquida_toneladas'] = (
    -1 * df_long.loc[mascara_remocao, 'emissao_toneladas'].abs()
)

n_remocoes = mascara_remocao.sum()
n_emissoes = (~mascara_remocao).sum()
print(f"  Emissoes (positivas): {n_emissoes:,} linhas")
print(f"  Remocoes (negativas): {n_remocoes:,} linhas")
print(f"  Coluna 'emissao_liquida_toneladas' criada")

# ============================================================
# CELULA 7 -- ETAPA 3: Filtros de qualidade
# ============================================================
# Equivalente SQL:
#   WHERE emissao IS NOT NULL
#     AND Estado IS NOT NULL
#     AND TRIM(Estado) != ''
#
# Remove linhas sem valor de emissao ou sem estado definido.

print("\n" + "=" * 60)
print("PASSO 5: Aplicando filtros de qualidade...")
print("=" * 60)

linhas_antes = len(df_long)

# Filtro 1: emissao nao pode ser nula
filtro_emissao = df_long['emissao_toneladas'].notna()
removidas_emissao = (~filtro_emissao).sum()

# Filtro 2: estado nao pode ser nulo ou vazio
filtro_estado = df_long['estado'].notna() & (df_long['estado'] != '')
removidas_estado = (~filtro_estado).sum()

# Aplicar ambos os filtros
df_long = df_long[filtro_emissao & filtro_estado].copy()

linhas_depois = len(df_long)
print(f"  Linhas antes:  {linhas_antes:,}")
print(f"  Removidas (emissao nula):  {removidas_emissao:,}")
print(f"  Removidas (estado vazio):  {removidas_estado:,}")
print(f"  Linhas depois: {linhas_depois:,}")
print(f"  Taxa de retencao: {linhas_depois/linhas_antes*100:.1f}%")

# ============================================================
# CELULA 8 -- METADADOS DE LINHAGEM
# ============================================================
# Equivalente SQL:
#   CURRENT_TIMESTAMP() AS _processed_at,
#   'bronze.ext_bronze_seeg_raw_all' AS _source_table
#
# Adiciona informacoes de rastreabilidade para auditoria.

print("\n" + "=" * 60)
print("PASSO 6: Adicionando metadados de linhagem...")
print("=" * 60)

df_long['_processed_at'] = TIMESTAMP
df_long['_source_table'] = 'dados/00.raw/seeg_all.csv'
df_long['_camada'] = CAMADA

print(f"  Metadados adicionados: _processed_at, _source_table, _camada")

# ============================================================
# CELULA 9 -- REORGANIZAR COLUNAS
# ============================================================
# Organiza as colunas na mesma ordem logica do SQL.

print("\n" + "=" * 60)
print("PASSO 7: Organizando colunas finais...")
print("=" * 60)

colunas_finais = [
    # Temporal
    'ano',
    # Geografico
    'estado', 'bioma',
    # Setorial (hierarquia IPCC -- niveis 1 a 3 + atividade)
    'setor_nivel1', 'setor_nivel2', 'setor_nivel3',
    'atividade_geral',
    # Recorte
    'recorte',
    # Tipo de emissao e gas
    'tipo_emissao', 'gas',
    # Valores
    'emissao_toneladas', 'emissao_liquida_toneladas',
    # Metadados de linhagem
    '_processed_at', '_source_table', '_camada',
]

df_silver = df_long[colunas_finais].copy()

# Ordenar por ano, estado, setor
df_silver = df_silver.sort_values(
    ['ano', 'estado', 'setor_nivel1', 'setor_nivel2'],
    ignore_index=True
)

print(f"  {len(colunas_finais)} colunas organizadas")
print(f"  Colunas: {list(df_silver.columns)}")

# Liberar memoria
del df_long

# ============================================================
# CELULA 10 -- VALIDACOES DE INTEGRIDADE
# ============================================================
# Verificar se o resultado esta consistente.

print("\n" + "=" * 60)
print("PASSO 8: Validacoes de integridade...")
print("=" * 60)

# V1: Dimensoes
print(f"  Dimensoes: {df_silver.shape[0]:,} linhas x {df_silver.shape[1]} colunas")

# V2: Periodo
anos = sorted(df_silver['ano'].unique())
print(f"  Periodo: {anos[0]} a {anos[-1]} ({len(anos)} anos)")

# V3: Setores
setores = sorted(df_silver['setor_nivel1'].dropna().unique())
print(f"  Setores ({len(setores)}): {setores}")

# V4: Estados
estados = sorted(df_silver['estado'].dropna().unique())
print(f"  Estados ({len(estados)}): {estados[:5]}... {estados[-3:]}")

# V5: Biomas
biomas = sorted(df_silver['bioma'].dropna().unique())
print(f"  Biomas ({len(biomas)}): {biomas}")

# V6: Gases
gases = sorted(df_silver['gas'].dropna().unique())
print(f"  Gases ({len(gases)})")

# V7: Tipos de emissao
tipos = sorted(df_silver['tipo_emissao'].dropna().unique())
print(f"  Tipos de emissao ({len(tipos)}): {tipos}")

# V8: Nulos restantes
nulos = df_silver.isnull().sum()
nulos_relevantes = nulos[nulos > 0]
if len(nulos_relevantes) > 0:
    print(f"  Nulos restantes (esperados em bioma, recorte):")
    for col, n in nulos_relevantes.items():
        print(f"    {col}: {n:,}")
else:
    print(f"  Sem nulos restantes")

# V9: Amostra
print(f"\n  Amostra dos dados (primeiras 5 linhas):")
print(df_silver.head().to_string())

# ============================================================
# CELULA 11 -- SALVAR ARQUIVO SILVER
# ============================================================

print("\n" + "=" * 60)
print("PASSO 9: Salvando arquivo Silver...")
print("=" * 60)

# Salvar como CSV (formato universal, UTF-8 com BOM para Excel)
df_silver.to_csv(CAMINHO_SILVER_CSV, index=False, encoding='utf-8-sig')
tamanho = os.path.getsize(CAMINHO_SILVER_CSV)
print(f"  CSV salvo: {CAMINHO_SILVER_CSV}")
print(f"  Tamanho: {tamanho / 1024**2:.1f} MB")

# ============================================================
# CELULA 12 -- RESUMO FINAL
# ============================================================

print("\n" + "=" * 60)
print("  TRANSFORMACAO CONCLUIDA COM SUCESSO!")
print("=" * 60)

print(f"""
RESUMO:
  Arquivo origem:  {CAMINHO_BRONZE}
  Arquivo destino: {CAMINHO_SILVER_CSV}
  
  Bronze: {332296:,} linhas x 46 colunas (formato wide)
  Silver: {df_silver.shape[0]:,} linhas x {df_silver.shape[1]} colunas (formato long)
  
  Periodo: {anos[0]} a {anos[-1]}
  Setores: {len(setores)}
  Estados: {len(estados)}
  Biomas:  {len(biomas)}
  Gases:   {len(gases)}
  
EQUIVALENCIA SQL -> PYTHON:
  UNPIVOT (35 colunas -> linhas) = pd.melt()
  REGEXP_REPLACE + CAST         = str.extract() + astype(int)
  TRIM()                        = str.strip()
  NULLIF(TRIM(), '')            = replace('', None)
  CASE WHEN LIKE '%remo%'       = str.contains('remo') + mascara
  CAST(emissao AS FLOAT64)      = pd.to_numeric(errors='coerce')
  WHERE emissao IS NOT NULL     = df[df['emissao'].notna()]
  CURRENT_TIMESTAMP()           = datetime.now().strftime()

Pronto para conexao com Power BI ou analise na Camada Gold!
""")
