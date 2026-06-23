import os
import pandas as pd
import numpy as np

def clean_and_transform_crop_yield():
    # Definir caminhos absolutos baseados no workspace do usuário
    base_dir = r"g:\.shortcut-targets-by-id\1LxU2y_h2XY8g0JiAOin2DcmjlXADV8uI\PROJETO_FINAL_GENERATION"
    input_path = os.path.join(base_dir, "dados", "01.bronze", "crop_yieldKAGGLE.csv", "crop_yield_bronze.csv")
    output_dir = os.path.join(base_dir, "dados", "02.silver")
    output_csv = os.path.join(output_dir, "crop_yield_silver.csv")
    output_parquet = os.path.join(output_dir, "crop_yield_silver.parquet")

    print(f"Lendo dados da camada Bronze de: {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo Bronze não encontrado em: {input_path}")

    # 1. Carregar dados brutos
    df = pd.read_csv(input_path, low_memory=False)
    initial_shape = df.shape
    print(f"Dados carregados. Linhas: {initial_shape[0]:,} | Colunas: {initial_shape[1]}")

    # 2. Remover duplicatas
    duplicadas_count = df.duplicated().sum()
    if duplicadas_count > 0:
        print(f"Removendo {duplicadas_count:,} linhas duplicadas...")
        df = df.drop_duplicates()
    else:
        print("Nenhuma linha duplicada encontrada.")

    # 3. Tratar valores nulos (se houver)
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        print("Valores nulos encontrados:")
        print(null_counts[null_counts > 0])
        print("Descartando linhas com valores nulos...")
        df = df.dropna()
    else:
        print("Nenhum valor nulo encontrado.")

    # 4. Traduzir e padronizar nomes de colunas
    # Mapeamento para português, em snake_case, sem acentuação para manter padrão
    mapping = {
        'Region': 'regiao',
        'Crop': 'cultura',
        'Soil_Type': 'tipo_solo',
        'Fertilizer_Used': 'fertilizante_utilizado',
        'Irrigation_Used': 'irrigacao_utilizada',
        'Rainfall_mm': 'chuva_mm',
        'Temperature_Celsius': 'temperatura_celsius',
        'Yield_tons_per_hectare': 'produtividade_ton_ha'
    }
    df = df.rename(columns=mapping)
    print("Colunas traduzidas e padronizadas.")

    # 5. Correção de tipos de dados
    # Garantir strings limpas
    for col in ['regiao', 'cultura', 'tipo_solo']:
        df[col] = df[col].astype(str).str.strip()

    # Garantir booleanos corretos
    df['fertilizante_utilizado'] = df['fertilizante_utilizado'].astype(bool)
    df['irrigacao_utilizada'] = df['irrigacao_utilizada'].astype(bool)

    # Garantir floats numéricos
    for col in ['chuva_mm', 'temperatura_celsius', 'produtividade_ton_ha']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 6. Remover anomalias de produtividade (valores negativos)
    # Produtividade (Yield) física não pode ser negativa
    negativos_count = (df['produtividade_ton_ha'] < 0).sum()
    if negativos_count > 0:
        print(f"Detectadas {negativos_count:,} linhas com produtividade negativa. Descartando registros anômalos...")
        df = df[df['produtividade_ton_ha'] >= 0]
    else:
        print("Nenhum registro com produtividade negativa encontrado.")

    # 7. Validação de faixas de valores
    print("\nEstatísticas finais das colunas numéricas:")
    print(df[['chuva_mm', 'temperatura_celsius', 'produtividade_ton_ha']].describe())

    # 8. Salvar arquivo limpo na camada Silver
    print(f"\nSalvando dados na camada Silver...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Salvar em CSV
    df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"Salvo CSV com sucesso em: {output_csv}")
    
    # Salvar em Parquet para melhor performance e armazenamento compactado
    try:
        df.to_parquet(output_parquet, index=False)
        print(f"Salvo Parquet com sucesso em: {output_parquet}")
    except ImportError:
        print("Aviso: Suporte a Parquet indisponível no ambiente Python atual (pyarrow/fastparquet não instalados). Pulando salvamento Parquet.")

    final_shape = df.shape
    print(f"\nProcessamento concluído com sucesso!")
    print(f"Registros iniciais: {initial_shape[0]:,} | Registros finais: {final_shape[0]:,}")
    print(f"Diferença (linhas descartadas): {initial_shape[0] - final_shape[0]:,}")

if __name__ == "__main__":
    clean_and_transform_crop_yield()
