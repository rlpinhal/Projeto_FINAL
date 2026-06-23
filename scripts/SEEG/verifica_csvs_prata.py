# ============================================================
# SCRIPT: Validador de Qualidade de Dados Silver SEEG
# ============================================================
# Projeto: Inteligência Agroambiental — Créditos de Carbono ESG
# Diretorio dos CSVs: dados/02.silver/SEEG/
# Data: Junho/2026
#
# Descrição:
#   Realiza testes automatizados nos arquivos CSV gerados para
#   garantir conformidade com os requisitos da camada Silver
#   (UTF-8 puro, sem acentos, sem colunas fantasmas, sem strings
#   corrompidas ou translation missing, dtypes corretos).
# ============================================================

import os
import pandas as pd
import re

PASTA_SILVER = r"G:\.shortcut-targets-by-id\1LxU2y_h2XY8g0JiAOin2DcmjlXADV8uI\PROJETO_FINAL_GENERATION\dados\02.silver\SEEG"

CSV_FILES = [
    'emissao_regiao.csv',
    'emissao_subcategoria.csv',
    'emissao_total_setores.csv',
    'emissao_por_bioma.csv',
    'emissao_categoria.csv',
    'emissao_atividade_geral.csv',
    'emissao_por_estado.csv',
]

def contains_special_chars(text):
    """Retorna True se o texto contiver acentos, cedilhas ou caracteres especiais do portugues."""
    if not isinstance(text, str):
        return False
    # Regex para capturar acentos comuns do portugues (ã, á, é, í, ó, ú, ç, ô, ê, etc.) e caracteres corrompidos
    # Permitimos letras ASCII, numeros, underlines, espacos e caracteres basicos (hifens, parenteses)
    pattern = re.compile(r'[^\x00-\x7F]')
    return bool(pattern.search(text))

def run_tests():
    print("=" * 60)
    print("STARTING AUTOMATED TESTS - SILVER LAYER SEEG")
    print("=" * 60)
    
    erros_totais = 0
    
    for csv_file in CSV_FILES:
        caminho_csv = os.path.join(PASTA_SILVER, csv_file)
        print(f"\nValidating: {csv_file}")
        
        if not os.path.exists(caminho_csv):
            print(f"  ERROR: File not found: {caminho_csv}")
            erros_totais += 1
            continue
            
        try:
            # 1. Testar se carrega como UTF-8
            df = pd.read_csv(caminho_csv, encoding='utf-8')
            print(f"  OK UTF-8: Loaded successfully ({len(df)} rows x {len(df.columns)} columns)")
            
            # 2. Testar se ha colunas fantasmas ou Unnamed
            unnamed_cols = [col for col in df.columns if "unnamed" in str(col).lower()]
            if unnamed_cols:
                print(f"  ERROR: Unnamed columns found: {unnamed_cols}")
                erros_totais += 1
            else:
                print("  OK Unnamed columns: None found")
                
            # 3. Testar acentos e caracteres especiais nos cabecalhos
            header_errors = [col for col in df.columns if contains_special_chars(col)]
            if header_errors:
                print(f"  ERROR: Special characters in headers: {header_errors}")
                erros_totais += 1
            else:
                print("  OK Headers: No special characters")
                
            # 4. Testar acentos e caracteres especiais nos valores textuais das colunas
            value_errors = {}
            colunas_texto = [col for col in df.columns if df[col].dtype == 'object' or df[col].dtype == 'str']
            
            for col in colunas_texto:
                # Verifica se algum valor contem acentos ou caracteres especiais
                bad_values = df[df[col].apply(contains_special_chars)][col].unique()
                if len(bad_values) > 0:
                    value_errors[col] = list(bad_values)[:5]
                    
            if value_errors:
                print(f"  ERROR: Special characters in row values:")
                for col, vals in value_errors.items():
                    print(f"    - Column '{col}': {vals}...")
                erros_totais += len(value_errors)
            else:
                print("  OK Row values: No special characters")
                
            # 5. Testar "translation missing" nas celulas
            tm_errors = 0
            for col in df.columns:
                mask_tm = df[col].astype(str).str.lower().str.contains("translation.*missing", regex=True)
                if mask_tm.any():
                    tm_errors += mask_tm.sum()
                    
            if tm_errors > 0:
                print(f"  ERROR: Translation missing count: {tm_errors}")
                erros_totais += 1
            else:
                print("  OK System strings: No translation missing")
                
            # 6. Testar dtypes corretos
            if 'ano' in df.columns:
                if df['ano'].dtype not in ['int64', 'int32']:
                    print(f"  ERROR: Year column type must be integer: {df['ano'].dtype}")
                    erros_totais += 1
                else:
                    print("  OK Year column type: Correct")
                    
            numeric_cols = [col for col in df.columns if 'emissao' in col or 'valor' in col]
            bad_num_types = [col for col in numeric_cols if df[col].dtype not in ['float64', 'float32']]
            if bad_num_types:
                print(f"  ERROR: Metric column types must be float: {bad_num_types}")
                erros_totais += 1
            else:
                if numeric_cols:
                    print(f"  OK Metric column type: Correct")
                    
            # 7. Verificar se ha nulos remanescentes em colunas criticas
            nulls = df.isnull().sum().sum()
            if nulls > 0:
                print(f"  ERROR: Null values count: {nulls}")
                erros_totais += 1
            else:
                print("  OK Integrity: Zero null values")
                
        except Exception as e:
            print(f"  ERROR Critical error processing file: {e}")
            erros_totais += 1
            
    print("\n" + "=" * 60)
    if erros_totais == 0:
        print("ALL TESTS PASSED SUCCESSFULLY!")
    else:
        print(f"TESTS COMPLETED WITH {erros_totais} FAILURES.")
    print("=" * 60)
    return erros_totais == 0

if __name__ == '__main__':
    run_tests()
