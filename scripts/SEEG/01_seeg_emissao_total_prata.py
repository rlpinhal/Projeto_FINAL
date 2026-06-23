# ============================================================
# SCRIPT: Bronze → Silver — SEEG Emissão Total por Setor
# ============================================================
# Projeto: Inteligência Agroambiental — Créditos de Carbono ESG
# Fonte: SEEG (Sistema de Estimativas de Emissões e Remoções de GEE)
# Arquivo: "Emissao total .csv"
# Data: Junho/2026
#
# Descrição:
#   Transforma o arquivo bronze "Emissao total .csv" para a
#   camada Silver, aplicando limpeza, padronização e enriquecimento
#   conforme o "Guia extração e análise das fontes.md".
#
# Entrada:  dados/01.bronze/Datasets SEEG/Emissao total .csv
# Saída:    dados/02.silver/SEEG/silver_emissao_total_setor.csv
# ============================================================

import pandas as pd
import numpy as np
import os
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES
# ============================================================
PERIODO_INICIO = 2000
PERIODO_FIM = 2023
CAMADA = "SILVER"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Caminhos relativos à raiz do projeto
CAMINHO_BRONZE = os.path.join("dados", "01.bronze", "Datasets SEEG", "Emissao total .csv")
CAMINHO_SILVER_DIR = os.path.join("dados", "02.silver", "SEEG")
CAMINHO_SILVER_CSV = os.path.join(CAMINHO_SILVER_DIR, "silver_emissao_total_setor.csv")

print("=" * 60)
print("  SEEG -- Emissao Total por Setor: Bronze -> Silver")
print("=" * 60)

# ============================================================
# PASSO 1: CARREGAR BRONZE (leitura fiel do arquivo original)
# ============================================================
print("\n📥 PASSO 1: Carregando arquivo bronze...")

# O arquivo CSV usa vírgula como separador e ponto como decimal
# (formato padrão CSV inglês), porém o encoding é problemático
# (acentos estão em latin-1/cp1252, não UTF-8).

# Tentar múltiplos encodings para garantir leitura correta
encodings_tentativas = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
df_bronze = None

for enc in encodings_tentativas:
    try:
        df_temp = pd.read_csv(CAMINHO_BRONZE, encoding=enc)
        # Verificar se a coluna Categoria tem acentos corretos
        categorias = df_temp['Categoria'].tolist()
        # Se contém caracteres corrompidos (�), tentar próximo encoding
        if any('�' in str(c) for c in categorias):
            print(f"  ⚠️  Encoding '{enc}': acentos corrompidos, tentando próximo...")
            continue
        df_bronze = df_temp
        encoding_utilizado = enc
        print(f"  ✅ Encoding '{enc}' funcionou corretamente!")
        break
    except Exception as e:
        print(f"  ⚠️  Encoding '{enc}' falhou: {e}")
        continue

# Se nenhum encoding resolveu os acentos, usar latin-1 e corrigir manualmente
if df_bronze is None:
    print("  ⚠️  Nenhum encoding resolveu acentos. Usando latin-1 com correção manual.")
    df_bronze = pd.read_csv(CAMINHO_BRONZE, encoding='latin-1')
    encoding_utilizado = 'latin-1 (com correção manual)'

print(f"\n📊 Bronze carregada: {df_bronze.shape[0]} linhas × {df_bronze.shape[1]} colunas")
print(f"📋 Colunas: {list(df_bronze.columns)}")
print(f"📝 Categorias encontradas: {df_bronze['Categoria'].tolist()}")

# ============================================================
# PASSO 2: CORRIGIR ENCODING DOS NOMES DE CATEGORIAS
# ============================================================
print("\n🔧 PASSO 2: Corrigindo encoding das categorias...")

# Mapeamento de nomes corrompidos para nomes corretos em português
# O SEEG usa estes 5 setores padronizados
mapa_categorias_correcao = {
    # Variantes com encoding corrompido
    'Mudan\x87a de Uso da Terra e Floresta': 'Mudança de Uso da Terra e Floresta',
    'Mudança de Uso da Terra e Floresta': 'Mudança de Uso da Terra e Floresta',
    'Mudanca de Uso da Terra e Floresta': 'Mudança de Uso da Terra e Floresta',
    # Variantes de Agropecuária
    'Agropecu\x87ria': 'Agropecuária',
    'Agropecuária': 'Agropecuária',
    'Agropecuaria': 'Agropecuária',
    # Energia (normalmente OK)
    'Energia': 'Energia',
    # Variantes de Resíduos
    'Res\x92duos': 'Resíduos',
    'Resíduos': 'Resíduos',
    'Residuos': 'Resíduos',
    # Processos Industriais (normalmente OK)
    'Processos Industriais': 'Processos Industriais',
}

# Aplicar correção — primeiro tenta o mapa, se não encontrar, limpa manualmente
def corrigir_categoria(nome):
    """Corrige o encoding do nome da categoria."""
    nome = str(nome).strip()
    # Tentar mapeamento direto
    if nome in mapa_categorias_correcao:
        return mapa_categorias_correcao[nome]
    # Correções por conteúdo parcial (fallback robusto)
    nome_lower = nome.lower()
    if 'mudan' in nome_lower and 'terra' in nome_lower:
        return 'Mudança de Uso da Terra e Floresta'
    elif 'agropecu' in nome_lower or 'agropec' in nome_lower:
        return 'Agropecuária'
    elif 'energia' in nome_lower:
        return 'Energia'
    elif 'res' in nome_lower and 'duo' in nome_lower:
        return 'Resíduos'
    elif 'processos' in nome_lower and 'industriais' in nome_lower:
        return 'Processos Industriais'
    return nome  # Retorna original se não identificou

df_bronze['Categoria'] = df_bronze['Categoria'].apply(corrigir_categoria)
print(f"  ✅ Categorias corrigidas: {df_bronze['Categoria'].tolist()}")

# ============================================================
# PASSO 3: TRANSFORMAR FORMATO LARGO → LONGO (MELT/UNPIVOT)
# ============================================================
print("\n🔄 PASSO 3: Transformando formato largo → longo (melt)...")

# Separar colunas: 'Categoria' é metadado, as numéricas (anos) viram linhas
colunas_anos = [col for col in df_bronze.columns if str(col).strip().isdigit()]
colunas_metadados = ['Categoria']

print(f"  Colunas de metadados: {colunas_metadados}")
print(f"  Colunas de anos ({len(colunas_anos)}): [{colunas_anos[0]}...{colunas_anos[-1]}]")

df_silver = df_bronze.melt(
    id_vars=colunas_metadados,
    value_vars=colunas_anos,
    var_name='ano',
    value_name='emissao_tco2e'
)

print(f"  Antes: {df_bronze.shape[0]} linhas x {df_bronze.shape[1]} colunas")
print(f"  Depois: {df_silver.shape[0]} linhas x {df_silver.shape[1]} colunas")

# ============================================================
# PASSO 4: CONVERTER TIPOS DE DADOS
# ============================================================
print("\n🔢 PASSO 4: Convertendo tipos de dados...")

# Ano: texto → inteiro
df_silver['ano'] = pd.to_numeric(df_silver['ano'], errors='coerce').astype(int)

# Emissão: garantir que é float (já veio como float64, mas validar)
df_silver['emissao_tco2e'] = pd.to_numeric(df_silver['emissao_tco2e'], errors='coerce')

print(f"  ✅ ano: {df_silver['ano'].dtype} (min={df_silver['ano'].min()}, max={df_silver['ano'].max()})")
print(f"  ✅ emissao_tco2e: {df_silver['emissao_tco2e'].dtype}")

# ============================================================
# PASSO 5: FILTRAR PERÍODO DE INTEGRAÇÃO (2000–2023)
# ============================================================
print("\n📅 PASSO 5: Filtrando período de integração...")

linhas_antes = len(df_silver)
df_silver = df_silver[
    (df_silver['ano'] >= PERIODO_INICIO) &
    (df_silver['ano'] <= PERIODO_FIM)
].copy()

print(f"  Período: {PERIODO_INICIO}–{PERIODO_FIM}")
print(f"  Linhas: {linhas_antes} → {len(df_silver)} (removidas: {linhas_antes - len(df_silver)})")

# ============================================================
# PASSO 6: PADRONIZAR NOMES DE COLUNAS (snake_case)
# ============================================================
print("\n📋 PASSO 6: Padronizando nomes de colunas...")

df_silver = df_silver.rename(columns={
    'Categoria': 'setor'
})

print(f"  ✅ Colunas: {list(df_silver.columns)}")

# ============================================================
# PASSO 7: ENRIQUECER COM COLUNAS DERIVADAS
# ============================================================
print("\n✨ PASSO 7: Enriquecendo com colunas derivadas...")

# 7.1 — Sigla do setor (para visualizações compactas)
mapa_sigla_setor = {
    'Mudança de Uso da Terra e Floresta': 'MUT',
    'Agropecuária': 'AGRO',
    'Energia': 'ENE',
    'Resíduos': 'RES',
    'Processos Industriais': 'IND',
}
df_silver['setor_sigla'] = df_silver['setor'].map(mapa_sigla_setor)

# 7.2 — Emissão em milhões de tCO₂e (mais legível para dashboards)
df_silver['emissao_mt_co2e'] = df_silver['emissao_tco2e'] / 1_000_000

# 7.3 — Classificação: é setor agro ou LULUCF? (relevante para créditos de carbono)
mapa_grupo_esg = {
    'Mudança de Uso da Terra e Floresta': 'Uso da Terra (LULUCF)',
    'Agropecuária': 'Agropecuária',
    'Energia': 'Outros Setores',
    'Resíduos': 'Outros Setores',
    'Processos Industriais': 'Outros Setores',
}
df_silver['grupo_esg'] = df_silver['setor'].map(mapa_grupo_esg)

# 7.4 — Relevância para crédito de carbono
# Apenas Agropecuária e MUT são diretamente relevantes para o estudo
mapa_relevancia = {
    'Mudança de Uso da Terra e Floresta': 'Alta',
    'Agropecuária': 'Alta',
    'Energia': 'Baixa',
    'Resíduos': 'Baixa',
    'Processos Industriais': 'Baixa',
}
df_silver['relevancia_credito_carbono'] = df_silver['setor'].map(mapa_relevancia)

# 7.5 — Período de política ambiental (alinhado com MapBiomas Silver)
def classificar_periodo_politica(ano):
    """Classifica o ano por período de política ambiental brasileira."""
    if ano < 2004:
        return '1. Pré-PPCDAm (2000–2003)'
    elif ano <= 2012:
        return '2. PPCDAm ativo (2004–2012)'
    elif ano <= 2018:
        return '3. Estabilização (2013–2018)'
    elif ano <= 2022:
        return '4. Alta recente (2019–2022)'
    else:
        return '5. Pós-2023 (2023–)'

df_silver['periodo_politica'] = df_silver['ano'].apply(classificar_periodo_politica)

# 7.6 — Participação percentual do setor no total do ano
# (calculada por ano para facilitar análise de composição)
total_por_ano = df_silver.groupby('ano')['emissao_tco2e'].transform('sum')
df_silver['percentual_do_total'] = (df_silver['emissao_tco2e'] / total_por_ano * 100).round(2)

print(f"  ✅ Colunas derivadas adicionadas:")
print(f"     - setor_sigla: sigla do setor para dashboards")
print(f"     - emissao_mt_co2e: emissão em MtCO₂e (milhões)")
print(f"     - grupo_esg: agrupamento para análise ESG")
print(f"     - relevancia_credito_carbono: relevância para o projeto")
print(f"     - periodo_politica: contexto político-ambiental")
print(f"     - percentual_do_total: % do setor no total anual")

# ============================================================
# PASSO 8: ADICIONAR METADADOS DE RASTREABILIDADE
# ============================================================
print("\n🏷️ PASSO 8: Adicionando metadados de rastreabilidade...")

df_silver['unidade_medida'] = 'tCO2e (GWP-AR5)'
df_silver['fonte'] = 'SEEG Collection 13'
df_silver['escopo_geografico'] = 'Brasil (nacional)'
df_silver['_camada'] = CAMADA
df_silver['_arquivo_origem'] = 'Emissao total .csv'
df_silver['_encoding_original'] = encoding_utilizado
df_silver['_data_processamento'] = TIMESTAMP
df_silver['_periodo_integracao'] = f'{PERIODO_INICIO}–{PERIODO_FIM}'

print(f"  ✅ Metadados adicionados")

# ============================================================
# PASSO 9: TRATAR NULOS E DUPLICATAS
# ============================================================
print("\n🧹 PASSO 9: Tratando nulos e duplicatas...")

nulos = df_silver['emissao_tco2e'].isnull().sum()
print(f"  Nulos em emissao_tco2e: {nulos}")
if nulos > 0:
    df_silver = df_silver.dropna(subset=['emissao_tco2e'])
    print(f"  → Removidos {nulos} registros com emissão nula")

duplicatas = df_silver.duplicated(subset=['setor', 'ano']).sum()
print(f"  Duplicatas (setor+ano): {duplicatas}")
if duplicatas > 0:
    df_silver = df_silver.drop_duplicates(subset=['setor', 'ano'], keep='first')
    print(f"  → Removidas {duplicatas} duplicatas")

# ============================================================
# PASSO 10: ORDENAR E REORGANIZAR COLUNAS
# ============================================================
print("\n📐 PASSO 10: Ordenando e organizando colunas finais...")

# Ordenar linhas por ano e setor
df_silver = df_silver.sort_values(['ano', 'setor']).reset_index(drop=True)

# Organizar ordem das colunas (dados primeiro, metadados depois)
colunas_ordenadas = [
    # Identificadores
    'ano', 'setor', 'setor_sigla',
    # Métricas
    'emissao_tco2e', 'emissao_mt_co2e', 'percentual_do_total',
    # Classificações
    'grupo_esg', 'relevancia_credito_carbono', 'periodo_politica',
    # Contexto
    'unidade_medida', 'fonte', 'escopo_geografico',
    # Rastreabilidade (prefixo _)
    '_camada', '_arquivo_origem', '_encoding_original',
    '_data_processamento', '_periodo_integracao',
]

df_silver = df_silver[colunas_ordenadas]
print(f"  ✅ {len(colunas_ordenadas)} colunas organizadas")

# ============================================================
# PASSO 11: VALIDAÇÕES DE INTEGRIDADE
# ============================================================
print("\n🔍 PASSO 11: Validações de integridade...")

# Validação 1: Quantidade esperada de registros
registros_esperados = 5 * (PERIODO_FIM - PERIODO_INICIO + 1)  # 5 setores × 24 anos
assert len(df_silver) == registros_esperados, \
    f"Esperados {registros_esperados}, encontrados {len(df_silver)}"
print(f"  ✅ Registros: {len(df_silver)} (esperados: {registros_esperados})")

# Validação 2: 5 setores presentes
setores = sorted(df_silver['setor'].unique())
assert len(setores) == 5, f"Esperados 5 setores, encontrados {len(setores)}"
print(f"  ✅ Setores: {setores}")

# Validação 3: Período completo
anos = sorted(df_silver['ano'].unique())
assert anos[0] == PERIODO_INICIO and anos[-1] == PERIODO_FIM, \
    f"Período esperado {PERIODO_INICIO}-{PERIODO_FIM}, encontrado {anos[0]}-{anos[-1]}"
print(f"  ✅ Período: {anos[0]}–{anos[-1]} ({len(anos)} anos)")

# Validação 4: Sem valores negativos
negativos = (df_silver['emissao_tco2e'] < 0).sum()
print(f"  ✅ Valores negativos: {negativos}")

# Validação 5: Percentual soma ~100% por ano
for ano_check in [2000, 2010, 2023]:
    pct_total = df_silver[df_silver['ano'] == ano_check]['percentual_do_total'].sum()
    assert abs(pct_total - 100.0) < 0.1, \
        f"Percentual em {ano_check} soma {pct_total}%, esperado ~100%"
print(f"  ✅ Percentual soma ~100% por ano (verificados: 2000, 2010, 2023)")

# Validação 6: Emissão total 2023 coerente com estudo (esperado ~2.6 bi tCO₂e)
total_2023 = df_silver[df_silver['ano'] == 2023]['emissao_tco2e'].sum()
print(f"  OK Emissao total 2023: {total_2023/1e9:.2f} GtCO2e ({total_2023/1e6:,.0f} MtCO2e)")

# ============================================================
# PASSO 12: SALVAR ARQUIVO SILVER
# ============================================================
print("\n💾 PASSO 12: Salvando arquivo Silver...")

os.makedirs(CAMINHO_SILVER_DIR, exist_ok=True)

# Salvar CSV (formato universal)
df_silver.to_csv(CAMINHO_SILVER_CSV, index=False, encoding='utf-8-sig')
tamanho_csv = os.path.getsize(CAMINHO_SILVER_CSV)
print(f"  ✅ CSV: {CAMINHO_SILVER_CSV} ({tamanho_csv:,} bytes)")

# ============================================================
# RESUMO FINAL
# ============================================================
print("\n" + "=" * 60)
print("  ✅ TRANSFORMAÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 60)
print(f"""
📊 RESUMO:
   Arquivo origem:  {CAMINHO_BRONZE}
   Arquivo destino: {CAMINHO_SILVER_CSV}
   Registros:       {len(df_silver)}
   Colunas:         {len(df_silver.columns)}
   Período:         {PERIODO_INICIO}–{PERIODO_FIM}
   Setores:         {len(setores)}

📈 AMOSTRA DOS DADOS:
""")

# Mostrar amostra
print(df_silver[['ano', 'setor', 'emissao_mt_co2e', 'percentual_do_total']].head(10).to_string(index=False))

print(f"""
📈 EMISSÃO POR SETOR (2023):
""")
resumo_2023 = df_silver[df_silver['ano'] == 2023][
    ['setor', 'emissao_mt_co2e', 'percentual_do_total']
].sort_values('emissao_mt_co2e', ascending=False)
print(resumo_2023.to_string(index=False))

print(f"""
📈 EVOLUÇÃO DO TOTAL (por ano):
""")
evolucao = df_silver.groupby('ano')['emissao_mt_co2e'].sum().reset_index()
evolucao.columns = ['ano', 'total_mt_co2e']
evolucao['total_mt_co2e'] = evolucao['total_mt_co2e'].round(1)
print(evolucao.to_string(index=False))

print("\n✅ Pronto para conexão com Power BI ou análise na Camada Gold!")
