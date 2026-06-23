"""
============================================================================
  TRANSFORMAÇÃO BRONZE → PRATA: MapBiomas Uso e Cobertura do Solo (Nível 1)
  ----- VERSÃO PARA GOOGLE COLAB -----
============================================================================

  INSTRUÇÕES DE USO NO COLAB:
  1. Crie um novo notebook no Google Colab
  2. Na primeira célula, monte o Google Drive:
       from google.colab import drive
       drive.mount('/content/drive')
  3. Na segunda célula, cole TODO o conteúdo deste arquivo e execute

  Fonte Bronze : dados/01.bronze/mapbiomas/mapbiomas-uso-e-cobertura-solo.csv
  Destino Prata: dados/02.prata/mapbiomas/prata_cobertura_brasil_nivel1.csv
============================================================================
"""

# ============================================================================
# CÉLULA 1 - MONTAR GOOGLE DRIVE (executar separadamente no Colab)
# ============================================================================
# from google.colab import drive
# drive.mount('/content/drive')

# ============================================================================
# CÉLULA 2 - SCRIPT COMPLETO (colar e executar no Colab)
# ============================================================================

import pandas as pd
import re
import os
from datetime import datetime

# ============================================================================
# CONFIGURAÇÃO DE CAMINHOS
# ============================================================================

# Ajuste este caminho para o local do seu projeto no Google Drive
BASE_DIR = "/content/drive/MyDrive/PROJETO_FINAL_GENERATION"

INPUT_FILE  = os.path.join(BASE_DIR, "dados", "01.bronze", "mapbiomas", "mapbiomas-uso-e-cobertura-solo.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "dados", "02.prata", "mapbiomas", "prata_cobertura_brasil_nivel1.csv")

# Verificar se o arquivo de entrada existe
if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Arquivo bronze não encontrado em: {INPUT_FILE}\n"
        f"Verifique se o Google Drive está montado e o caminho BASE_DIR está correto."
    )

# ============================================================================
# CONSTANTES DE MAPEAMENTO
# ============================================================================

# Tradução das classes de nível 1 (EN → PT)
TRADUCAO_CLASSES = {
    "1. Forest": "1. Floresta",
    "2. Non Forest Natural Formation": "2. Formação Natural Não Florestal",
    "3. Farming": "3. Agropecuária",
    "4. Non vegetated area": "4. Área Não Vegetada",
    "5. Water and Marine Environment": "5. Água e Ambiente Marinho",
    "6. Not Observed": "6. Não Observado",
}

# Mapeamento de grupo de uso da terra
GRUPO_USO = {
    "1. Forest": "Vegetação Nativa",
    "2. Non Forest Natural Formation": "Vegetação Nativa",
    "3. Farming": "Agropecuária",
    "4. Non vegetated area": "Área Não Vegetada",
    "5. Water and Marine Environment": "Água",
    "6. Not Observed": "Não Observado",
}

# Colunas de classe no CSV bronze
COLUNAS_CLASSE = [
    "1. Forest",
    "2. Non Forest Natural Formation",
    "3. Farming",
    "4. Non vegetated area",
    "5. Water and Marine Environment",
    "6. Not Observed",
]

# Filtro temporal: apenas anos >= ANO_INICIO
ANO_INICIO = 2000

# Metadados fixos
COLECAO_MAPBIOMAS = "10.1"
ARQUIVO_ORIGEM = "MAPBIOMAS_USOECOBERTURASOLO_coverage10.1.csv"


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def converter_numero_brasileiro(valor_str):
    """
    Converte número no formato brasileiro para float.
    Ex: "609.269.154,93" → 609269154.93
    """
    if pd.isna(valor_str) or str(valor_str).strip() == "":
        return float("nan")
    s = str(valor_str).strip().strip('"')
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def extrair_ano(label):
    """Extrai o ano de 'Soma de 2000' → 2000."""
    match = re.search(r"(\d{4})", str(label))
    return int(match.group(1)) if match else 0


# ============================================================================
# TRANSFORMAÇÃO PRINCIPAL
# ============================================================================

print("=" * 70)
print("  TRANSFORMACAO BRONZE -> PRATA: Cobertura do Solo (Nivel 1)")
print("=" * 70)

# --- 1. Leitura do arquivo Bronze ---
print(f"\nLendo arquivo Bronze: {INPUT_FILE}")

# O CSV bronze tem 25 linhas de cabeçalho/metadados.
# Linha 26 (0-indexed: 25) contém o cabeçalho real:
#   Dados | 1. Forest | 2. Non Forest... | ... | Total Resultado
# As primeiras 5 colunas são vazias (offset da tabela pivot do MapBiomas).
df_raw = pd.read_csv(
    INPUT_FILE,
    skiprows=25,       # Pular 25 linhas de metadados/layout
    header=0,          # Primeira linha após skip = cabeçalho
    encoding="utf-8",
)

print(f"  Linhas lidas: {len(df_raw)}")
print(f"  Colunas: {list(df_raw.columns)}")

# --- 2. Identificar colunas ---
col_dados = None
colunas_classe_encontradas = {}

for col in df_raw.columns:
    col_str = str(col).strip()
    if col_str == "Dados":
        col_dados = col
    for classe in COLUNAS_CLASSE:
        if col_str == classe:
            colunas_classe_encontradas[classe] = col

if col_dados is None:
    raise ValueError("Coluna 'Dados' nao encontrada no arquivo bronze!")

print(f"  Coluna de rotulo: '{col_dados}'")
print(f"  Classes encontradas: {len(colunas_classe_encontradas)}/{len(COLUNAS_CLASSE)}")

# --- 3. Filtrar apenas linhas "Soma de XXXX" ---
df_dados = df_raw[df_raw[col_dados].astype(str).str.startswith("Soma de")].copy()
print(f"\nLinhas de dados encontradas: {len(df_dados)}")

# --- 4. Extrair ano e filtrar >= ANO_INICIO ---
df_dados["ano"] = df_dados[col_dados].apply(extrair_ano)
df_dados = df_dados[df_dados["ano"] >= ANO_INICIO].copy()
print(f"  Anos apos filtro (>= {ANO_INICIO}): {sorted(df_dados['ano'].unique())}")
print(f"  Registros restantes: {len(df_dados)}")

# --- 5. Unpivot (melt) das classes ---
registros = []
for _, row in df_dados.iterrows():
    ano = row["ano"]
    for classe_en, col_name in colunas_classe_encontradas.items():
        area_ha = converter_numero_brasileiro(row[col_name])
        registros.append({
            "ano": ano,
            "classe_nivel_1_en": classe_en,
            "area_ha": area_ha,
        })

df_prata = pd.DataFrame(registros)
print(f"\nRegistros apos unpivot: {len(df_prata)}")

# --- 6. Adicionar traducao e grupo de uso ---
df_prata["classe_nivel_1"] = df_prata["classe_nivel_1_en"].map(TRADUCAO_CLASSES)
df_prata["grupo_uso"] = df_prata["classe_nivel_1_en"].map(GRUPO_USO)

# --- 7. Adicionar metadados e colunas de linhagem ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
ano_min = int(df_prata["ano"].min())
ano_max = int(df_prata["ano"].max())
periodo = f"{ano_min}\u2013{ano_max}"  # en-dash Unicode

df_prata["pais"] = "Brasil"
df_prata["escopo_geografico"] = "Brasil (nacional)"
df_prata["nivel_classe"] = 1
df_prata["colecao_mapbiomas"] = COLECAO_MAPBIOMAS
df_prata["unidade_medida"] = "hectares"
df_prata["_camada"] = "SILVER"
df_prata["_arquivo_origem"] = ARQUIVO_ORIGEM
df_prata["_data_processamento"] = timestamp
df_prata["_periodo_integracao"] = periodo

# --- 8. Ordenar colunas na ordem final ---
colunas_finais = [
    "ano",
    "classe_nivel_1_en",
    "classe_nivel_1",
    "grupo_uso",
    "area_ha",
    "pais",
    "escopo_geografico",
    "nivel_classe",
    "colecao_mapbiomas",
    "unidade_medida",
    "_camada",
    "_arquivo_origem",
    "_data_processamento",
    "_periodo_integracao",
]
df_prata = df_prata[colunas_finais]

# --- 9. Resumo ---
print(f"\nDataFrame prata final:")
print(f"  Shape: {df_prata.shape}")
print(f"  Anos: {sorted(df_prata['ano'].unique())}")
print(f"  Classes: {df_prata['classe_nivel_1_en'].unique().tolist()}")
print(f"\nPrimeiras linhas:")
display(df_prata.head(12))

# --- 10. Salvar ---
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
df_prata.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
print(f"\nArquivo salvo em: {OUTPUT_FILE}")

# ============================================================================
# VALIDAÇÃO
# ============================================================================

print("\n" + "=" * 70)
print("  VALIDACAO DOS DADOS")
print("=" * 70)

# Recarregar bronze para comparacao
df_raw2 = pd.read_csv(INPUT_FILE, skiprows=25, header=0, encoding="utf-8")
df_val = df_raw2[df_raw2["Dados"].astype(str).str.startswith("Soma de")].copy()
df_val["ano"] = df_val["Dados"].apply(extrair_ano)
df_val = df_val[df_val["ano"] >= ANO_INICIO].copy()

erros = 0
total_checks = 0
for _, row_p in df_prata.iterrows():
    ano = row_p["ano"]
    classe_en = row_p["classe_nivel_1_en"]
    area_prata = row_p["area_ha"]
    row_b = df_val[df_val["ano"] == ano]
    if len(row_b) == 0:
        print(f"  ERRO: Ano {ano} nao encontrado no bronze!")
        erros += 1
        continue
    area_bronze = converter_numero_brasileiro(row_b.iloc[0][classe_en])
    total_checks += 1
    if abs(area_prata - area_bronze) > 0.01:
        print(f"  DIVERGENCIA: Ano={ano}, Classe='{classe_en}', Bronze={area_bronze:.2f}, Prata={area_prata:.2f}")
        erros += 1

n_anos = len(df_prata["ano"].unique())
n_classes = len(COLUNAS_CLASSE)
esperado = n_anos * n_classes

print(f"\nResultado da validacao:")
print(f"  Total de verificacoes: {total_checks}")
print(f"  Erros encontrados: {erros}")
print(f"  Registros esperados ({n_anos} anos x {n_classes} classes): {esperado}")
print(f"  Registros obtidos: {len(df_prata)}")
print(f"  Valores nulos em area_ha: {df_prata['area_ha'].isna().sum()}")

if erros == 0 and len(df_prata) == esperado:
    print("\n  TODOS OS VALORES CONFEREM COM O ARQUIVO BRONZE!")
    print("  Transformacao concluida com sucesso!")
else:
    print(f"\n  {erros} divergencias encontradas. Verificar os dados.")

print("\n" + "=" * 70)
