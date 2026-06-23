"""
============================================================================
  TRANSFORMAÇÃO BRONZE → PRATA: MapBiomas Uso e Cobertura do Solo (Nível 1)
============================================================================
  Fonte Bronze : dados/01.bronze/mapbiomas/mapbiomas-uso-e-cobertura-solo.csv
  Destino Prata: dados/02.prata/mapbiomas/prata_cobertura_brasil_nivel1.csv

  Descrição:
    - Lê o CSV bronze em formato de tabela pivot (exportado do MapBiomas)
    - Extrai as linhas de dados (linhas "Soma de YYYY")
    - Faz unpivot das colunas de classe para formato longo
    - Converte valores numéricos do formato brasileiro (ponto=milhar, vírgula=decimal)
    - Traduz nomes de classe EN → PT
    - Mapeia grupo de uso da terra
    - Filtra apenas anos >= 2000
    - Adiciona colunas de metadados e linhagem
    - Salva na camada Prata

  Para uso no Google Colab:
    1. Monte o Google Drive
    2. Ajuste BASE_DIR para o caminho correto no Drive
    3. Execute o script
============================================================================
"""

import pandas as pd
import re
from datetime import datetime


# ============================================================================
# CONFIGURAÇÃO DE CAMINHOS
# ============================================================================

# --- Para Google Colab: descomente e ajuste ---
# from google.colab import drive
# drive.mount('/content/drive')
# BASE_DIR = "/content/drive/MyDrive/PROJETO_FINAL_GENERATION"

# --- Para execução local ---
BASE_DIR = r"e:\My Drive\PROJETO_FINAL_GENERATION"

INPUT_FILE  = f"{BASE_DIR}/dados/01.bronze/mapbiomas/mapbiomas-uso-e-cobertura-solo.csv"
OUTPUT_FILE = f"{BASE_DIR}/dados/02.prata/mapbiomas/prata_cobertura_brasil_nivel1.csv"

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

# Colunas de classe no CSV bronze (cabeçalho na linha 26 do arquivo)
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

def converter_numero_brasileiro(valor_str: str) -> float:
    """
    Converte um número no formato brasileiro para float.
    Formato brasileiro: "609.269.154,93" → 609269154.93
    Remove pontos (separador de milhar) e troca vírgula por ponto (decimal).
    """
    if pd.isna(valor_str) or str(valor_str).strip() == "":
        return float("nan")
    s = str(valor_str).strip().strip('"')
    # Remover separador de milhar (ponto) e trocar vírgula por ponto decimal
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def extrair_ano(label: str) -> int:
    """
    Extrai o ano de um label como 'Soma de 2000' → 2000.
    """
    match = re.search(r"(\d{4})", str(label))
    if match:
        return int(match.group(1))
    return 0


# ============================================================================
# TRANSFORMAÇÃO PRINCIPAL
# ============================================================================

def transformar_bronze_para_prata():
    """
    Executa a transformação completa de Bronze → Prata.
    """
    print("=" * 70)
    print("  TRANSFORMAÇÃO BRONZE → PRATA: Cobertura do Solo (Nível 1)")
    print("=" * 70)

    # --- 1. Leitura do arquivo Bronze ---
    print(f"\n📂 Lendo arquivo Bronze: {INPUT_FILE}")

    # O CSV bronze tem 25 linhas de cabeçalho/metadados antes dos dados reais.
    # Linha 26 (0-indexed: 25) contém o cabeçalho: Dados, 1. Forest, 2. Non Forest..., Total Resultado
    # Linhas 27-66 (0-indexed: 26-65) contêm os dados.
    # As primeiras 5 colunas estão vazias (offset da tabela pivot).

    # Leitura bruta pulando as 25 primeiras linhas de metadados
    df_raw = pd.read_csv(
        INPUT_FILE,
        skiprows=25,       # Pular as 25 linhas de cabeçalho/layout
        header=0,          # Primeira linha após skip é o cabeçalho
        encoding="utf-8",
    )

    print(f"  → Linhas lidas: {len(df_raw)}")
    print(f"  → Colunas: {list(df_raw.columns)}")

    # --- 2. Identificar colunas corretas ---
    # O cabeçalho real está nos campos: Dados, class_level_1 columns, Total Resultado
    # Mas as primeiras 5 colunas são vazias (unnamed) pelo layout da planilha
    # Precisamos encontrar a coluna "Dados" e as colunas de classe

    # Renomear colunas unnamed para facilitar
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
        raise ValueError("Coluna 'Dados' não encontrada no arquivo bronze!")

    print(f"  → Coluna de rótulo: '{col_dados}'")
    print(f"  → Classes encontradas: {len(colunas_classe_encontradas)}/{len(COLUNAS_CLASSE)}")

    for classe in COLUNAS_CLASSE:
        if classe not in colunas_classe_encontradas:
            print(f"  ⚠️ Classe não encontrada: {classe}")

    # --- 3. Filtrar apenas linhas "Soma de XXXX" ---
    df_dados = df_raw[df_raw[col_dados].astype(str).str.startswith("Soma de")].copy()
    print(f"\n📊 Linhas de dados encontradas: {len(df_dados)}")

    # --- 4. Extrair ano ---
    df_dados["ano"] = df_dados[col_dados].apply(extrair_ano)
    print(f"  → Anos disponíveis: {sorted(df_dados['ano'].unique())}")

    # --- 5. Filtrar anos >= ANO_INICIO ---
    df_dados = df_dados[df_dados["ano"] >= ANO_INICIO].copy()
    print(f"  → Anos após filtro (>= {ANO_INICIO}): {sorted(df_dados['ano'].unique())}")
    print(f"  → Registros restantes: {len(df_dados)}")

    # --- 6. Unpivot (melt) das classes ---
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
    print(f"\n🔄 Registros após unpivot: {len(df_prata)}")

    # --- 7. Adicionar tradução e grupo de uso ---
    df_prata["classe_nivel_1"] = df_prata["classe_nivel_1_en"].map(TRADUCAO_CLASSES)
    df_prata["grupo_uso"] = df_prata["classe_nivel_1_en"].map(GRUPO_USO)

    # --- 8. Adicionar metadados e colunas de linhagem ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ano_min = int(df_prata["ano"].min())
    ano_max = int(df_prata["ano"].max())
    periodo = f"{ano_min}\u2013{ano_max}"  # en-dash

    df_prata["pais"] = "Brasil"
    df_prata["escopo_geografico"] = "Brasil (nacional)"
    df_prata["nivel_classe"] = 1
    df_prata["colecao_mapbiomas"] = COLECAO_MAPBIOMAS
    df_prata["unidade_medida"] = "hectares"
    df_prata["_camada"] = "SILVER"
    df_prata["_arquivo_origem"] = ARQUIVO_ORIGEM
    df_prata["_data_processamento"] = timestamp
    df_prata["_periodo_integracao"] = periodo

    # --- 9. Ordenar colunas na ordem final ---
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

    # --- 10. Resumo final ---
    print(f"\n✅ DataFrame prata final:")
    print(f"  → Shape: {df_prata.shape}")
    print(f"  → Colunas: {list(df_prata.columns)}")
    print(f"  → Anos: {sorted(df_prata['ano'].unique())}")
    print(f"  → Classes: {df_prata['classe_nivel_1_en'].unique().tolist()}")
    print(f"\n  Primeiras linhas:")
    print(df_prata.head(10).to_string(index=False))

    # --- 11. Salvar ---
    print(f"\n💾 Salvando em: {OUTPUT_FILE}")
    df_prata.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print("  → Arquivo salvo com sucesso!")

    return df_prata


# ============================================================================
# VALIDAÇÃO
# ============================================================================

def validar_resultado(df_prata: pd.DataFrame):
    """
    Valida o resultado comparando com os dados do bronze.
    """
    print("\n" + "=" * 70)
    print("  VALIDAÇÃO DOS DADOS")
    print("=" * 70)

    # Recarregar o bronze para comparação
    df_raw = pd.read_csv(INPUT_FILE, skiprows=25, header=0, encoding="utf-8")
    df_dados = df_raw[df_raw["Dados"].astype(str).str.startswith("Soma de")].copy()
    df_dados["ano"] = df_dados["Dados"].apply(extrair_ano)
    df_dados = df_dados[df_dados["ano"] >= ANO_INICIO].copy()

    erros = 0
    total_checks = 0

    for _, row_prata in df_prata.iterrows():
        ano = row_prata["ano"]
        classe_en = row_prata["classe_nivel_1_en"]
        area_prata = row_prata["area_ha"]

        # Encontrar valor correspondente no bronze
        row_bronze = df_dados[df_dados["ano"] == ano]
        if len(row_bronze) == 0:
            print(f"  ❌ Ano {ano} não encontrado no bronze!")
            erros += 1
            continue

        valor_bronze_str = row_bronze.iloc[0][classe_en]
        area_bronze = converter_numero_brasileiro(valor_bronze_str)

        total_checks += 1

        # Comparar com tolerância para arredondamento de float
        if abs(area_prata - area_bronze) > 0.01:
            print(f"  ❌ DIVERGÊNCIA: Ano={ano}, Classe='{classe_en}'")
            print(f"     Bronze: {area_bronze:.2f} | Prata: {area_prata:.2f}")
            print(f"     Diferença: {abs(area_prata - area_bronze):.4f}")
            erros += 1

    print(f"\n📋 Resultado da validação:")
    print(f"  → Total de verificações: {total_checks}")
    print(f"  → Erros encontrados: {erros}")

    if erros == 0:
        print("  ✅ TODOS OS VALORES CONFEREM COM O ARQUIVO BRONZE!")
    else:
        print(f"  ⚠️ {erros} divergências encontradas!")

    # Validações adicionais
    print(f"\n📊 Verificações de integridade:")

    # Número esperado de registros
    n_anos = len(df_prata["ano"].unique())
    n_classes = len(COLUNAS_CLASSE)
    esperado = n_anos * n_classes
    print(f"  → Registros esperados ({n_anos} anos × {n_classes} classes): {esperado}")
    print(f"  → Registros obtidos: {len(df_prata)}")
    if len(df_prata) == esperado:
        print("  ✅ Contagem correta!")
    else:
        print("  ❌ Contagem divergente!")

    # Verificar se não há valores nulos em area_ha
    nulos = df_prata["area_ha"].isna().sum()
    print(f"  → Valores nulos em area_ha: {nulos}")
    if nulos == 0:
        print("  ✅ Nenhum valor nulo!")
    else:
        print(f"  ❌ {nulos} valores nulos encontrados!")

    # Verificar todos os anos presentes
    anos_esperados_bronze = sorted(df_dados["ano"].unique())
    anos_prata = sorted(df_prata["ano"].unique())
    print(f"  → Anos no bronze (>= {ANO_INICIO}): {anos_esperados_bronze}")
    print(f"  → Anos na prata: {anos_prata}")
    if anos_esperados_bronze == anos_prata:
        print("  ✅ Todos os anos presentes!")
    else:
        print("  ❌ Divergência nos anos!")

    return erros == 0


# ============================================================================
# EXECUÇÃO
# ============================================================================

if __name__ == "__main__":
    df_resultado = transformar_bronze_para_prata()
    sucesso = validar_resultado(df_resultado)

    if sucesso:
        print("\n🎉 Transformação concluída com sucesso e validada!")
    else:
        print("\n⚠️ Transformação concluída, mas com divergências na validação.")

    print("\n" + "=" * 70)
