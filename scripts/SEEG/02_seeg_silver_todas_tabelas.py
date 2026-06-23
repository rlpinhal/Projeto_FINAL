# ============================================================
# SCRIPT: SEEG Excel → Silver CSVs (All Sheets)
# ============================================================
# Projeto: Inteligência Agroambiental — Créditos de Carbono ESG
# Fonte: SEEG (Sistema de Estimativas de Emissões e Remoções de GEE)
# Arquivo de Entrada: dados/02.silver/SEEG/SEEG Dados Arrumados.xlsx
# Data: Junho/2026
#
# Descrição:
#   Lê o arquivo Excel consolidado da SEEG, limpa todas as abas
#   removendo acentuação, corrigindo strings de sistema corrompidas,
#   eliminando colunas fantasmas e salvando cada aba como um arquivo CSV
#   otimizado para bancos de dados SQL na camada Silver.
# ============================================================

import pandas as pd
import numpy as np
import os
import unicodedata

# Caminhos
CAMINHO_EXCEL = r"G:\.shortcut-targets-by-id\1LxU2y_h2XY8g0JiAOin2DcmjlXADV8uI\PROJETO_FINAL_GENERATION\dados\02.silver\SEEG\SEEG Dados Arrumados.xlsx"
PASTA_DESTINO = r"G:\.shortcut-targets-by-id\1LxU2y_h2XY8g0JiAOin2DcmjlXADV8uI\PROJETO_FINAL_GENERATION\dados\02.silver\SEEG"

# Mapeamento de categorias corrompidas para nomes corrigidos sem acento
# (Inclui tratamento de caracteres corrompidos e padronização direta sem acento)
VALUE_MAP = {
    # Regiao
    'No Identificado': 'Nao Identificado',
    'Não Identificado': 'Nao Identificado',
    
    # Subcategoria
    'Processo de digesto de animais ruminantes': 'Processo de digestao de animais ruminantes',
    'Rodovirio': 'Rodoviario',
    'Deposio de dejetos em pastagem': 'Deposicao de dejetos em pastagem',
    'Disposio final em aterros sanitrios': 'Disposicao final em aterros sanitarios',
    'Produo de ferro gusa e ao': 'Producao de ferro gusa e aco',
    'Resduos agrcolas': 'Residuos agricolas',
    'Fertilizantes sintticos nitrogenados': 'Fertilizantes sinteticos nitrogenados',
    'Tratamento e disposio de dejetos animais': 'Tratamento e disposicao de dejetos animais',
    'Corretivo agrcola': 'Corretivo agricola',
    'Gerao de eletricidade (servio pblico)': 'Geracao de eletricidade (servico publico)',
    'Tratamento e despejo de efluentes domsticos': 'Tratamento e despejo de efluentes domesticos',
    'Refino de petrleo': 'Refino de petroleo',
    'Explorao de petrleo e gs natural': 'Exploracao de petroleo e gas natural',
    'Produo de cimento': 'Producao de cimento',
    'Agropecuria': 'Agropecuaria',
    'Qumica': 'Quimica',
    'Disposio em aterros controlados ou lixes': 'Disposicao em aterros controlados ou lixoes',
    'Areo': 'Aereo',
    'Regenerao': 'Regeneracao',
    'Outras mudanas de uso da terra': 'Outras mudancas de uso da terra',
    'Ferro gusa e ao': 'Ferro gusa e aco',
    'No ferrosos e outros da metalurgia': 'Nao ferrosos e outros da metalurgia',
    'Aplicao de resduos orgnicos': 'Aplicacao de residuos organicos',
    'Outras indstrias': 'Outras industrias',
    'Produo de cal': 'Producao de cal',
    
    # Total Setores
    'Mudana de Uso da Terra e Floresta': 'Mudanca de Uso da Terra e Floresta',
    'Resduos': 'Residuos',
    
    # Bioma
    'Amaznia': 'Amazonia',
    'Mata Atlntica': 'Mata Atlantica',
    
    # Categoria
    'Alteraes de uso da terra': 'Alteracoes de uso da terra',
    'Fermentao entrica': 'Fermentacao enterica',
    'Resduos florestais': 'Residuos florestais',
    'Disposio final': 'Disposicao final',
    'Produo de combustveis': 'Producao de combustiveis',
    'Produo de metais': 'Producao de metais',
    'Carbono orgnico no solo': 'Carbono organico no solo',
    'Efluentes domsticos': 'Efluentes domesticos',
    'Cultivo de arroz': 'Cultivo de arroz',
    'Produo e uso de HFCs': 'Producao e uso de HFCs',
    'Efluentes lquidos industriais': 'Efluentes liquidos industriais',
    'Indstria Qumica': 'Industria Quimica',
    'Incinerao ou queima a cu aberto': 'Incineracao ou queima a ceu aberto',
    'Pblico': 'Publico',
    'Uso no-energtico de combustveis e solventes em outros setores': 'Uso nao-energetico de combustiveis e solventes em outros setores',
    'Uso de SF6 em equipamentos eltricos': 'Uso de SF6 em equipamentos eletricos',
    'Queima de resduos agrcolas': 'Queima de residuos agricolas',
    'Tratamento biolgico de resduos slidos': 'Tratamento biologico de residuos solidos',
    'Produo e uso de CFs': 'Producao e uso de CFs',
    
    # Atividade Geral
    'Pecuria': 'Pecuaria',
    'Produo de combustveis': 'Producao de combustiveis',
    'Gerao de eletricidade': 'Geracao de eletricidade',
    'Outras matrias primas e indstrias': 'Outras materias primas e industrias',
    'Edificaes': 'Edificacoes',
    'Agropecuria (finalidade no identificada)': 'Agropecuaria (finalidade nao identificada)',
    'Vegetao nativa': 'Vegetacao nativa',
    
    # Estado
    'Par': 'Para',
    'Maranho': 'Maranhao',
    'So Paulo': 'Sao Paulo',
    'Rondnia': 'Rondonia',
    'Gois': 'Goias',
    'Paran': 'Parana',
    'Piau': 'Piaui',
    'Cear': 'Ceara',
    'Esprito Santo': 'Espirito Santo',
    'Paraba': 'Paraiba',
    'Amap': 'Amapa',
    'No Alocado': 'Nao Alocado',
    'Não Alocado': 'Nao Alocado',
}

# Mapeamento explícito de cabeçalhos das tabelas
HEADER_MAP = {
    'Regio': 'regiao',
    'Região': 'regiao',
    'Ano': 'ano',
    'Emisso (Mt)': 'emissao_mt',
    'Emissão (Mt)': 'emissao_mt',
    'Categoria': 'categoria',
    'Setor': 'setor',
    'Emissao(Mt)': 'emissao_mt',
    'Valor (Mt)': 'valor_mt',
}

# Mapeamento explícito das abas para os nomes dos arquivos CSV de destino
SHEET_FILE_MAP = {
    'Emissao Regiao ': 'emissao_regiao.csv',
    'Emissao subcategoria': 'emissao_subcategoria.csv',
    'Emisso Total Setores': 'emissao_total_setores.csv',
    'Emissao por bioma': 'emissao_por_bioma.csv',
    'Emissao Categoria': 'emissao_categoria.csv',
    'Emissao Atividade Geral': 'emissao_atividade_geral.csv',
    'Emissao por estado': 'emissao_por_estado.csv',
}

def remove_accents(text):
    """Remove acentuação e diacríticos de uma string usando normalização unicode."""
    if not isinstance(text, str):
        return text
    # Decompõe caracteres acentuados
    nfkd_form = unicodedata.normalize('NFKD', text)
    # Filtra os diacríticos
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def clean_text_value(val):
    """Limpa e padroniza os valores textuais das linhas."""
    if pd.isna(val):
        return "Nao Alocado"
    
    val_str = str(val).strip()
    
    # 1. Aplicar mapeamento de valores conhecidos para corrigir erros de encoding e tradução
    if val_str in VALUE_MAP:
        val_str = VALUE_MAP[val_str]
        
    # 2. Remover acentos restantes
    val_str = remove_accents(val_str)
    
    return val_str

def clean_header(header):
    """Limpa e padroniza cabeçalhos das colunas (snake_case, sem acentos)."""
    header_str = str(header).strip()
    
    # 1. Se estiver no mapa explícito, usar o mapeamento
    if header_str in HEADER_MAP:
        return HEADER_MAP[header_str]
    
    # 2. Fallback de limpeza geral
    cleaned = remove_accents(header_str).lower()
    cleaned = cleaned.replace(' ', '_').replace('(', '').replace(')', '').replace('$', '')
    return cleaned

def clean_sheet_name(sheet_name):
    """Gera um nome de arquivo seguro a partir do nome da aba."""
    if sheet_name in SHEET_FILE_MAP:
        return SHEET_FILE_MAP[sheet_name]
    
    # Fallback caso surja uma aba nova
    cleaned = remove_accents(sheet_name).strip().lower()
    cleaned = cleaned.replace(' ', '_')
    return f"{cleaned}.csv"

def run_etl():
    print("=" * 60)
    print("STARTING ETL: SEEG Excel -> Silver CSVs (SQL-Ready)")
    print("=" * 60)
    
    if not os.path.exists(CAMINHO_EXCEL):
        raise FileNotFoundError(f"Arquivo de entrada nao encontrado: {CAMINHO_EXCEL}")
        
    xl = pd.ExcelFile(CAMINHO_EXCEL)
    print(f"Abas encontradas no Excel: {xl.sheet_names}\n")
    
    for sheet_name in xl.sheet_names:
        print(f"--------------------------------------------------")
        print(f"Processing sheet: '{sheet_name}'")
        
        # Carrega os dados brutos da aba
        df = xl.parse(sheet_name)
        print(f"  Shape bruto: {df.shape[0]} linhas x {df.shape[1]} colunas")
        
        # ============================================================
        # 1. ELIMINAR LINHAS E COLUNAS FANTASMAS (TOTALMENTE VAZIAS)
        # ============================================================
        # Remove colunas fantasmas geradas na exportação (todas as células são NaN ou Unnamed)
        unnamed_cols = [col for col in df.columns if "Unnamed" in str(col)]
        df = df.drop(columns=[col for col in unnamed_cols if df[col].isna().all()], errors='ignore')
        
        # Remove colunas onde todos os valores são NaN
        df = df.dropna(axis=1, how='all')
        
        # Remove linhas totalmente vazias
        df = df.dropna(axis=0, how='all')
        
        # ============================================================
        # 2. LIMPAR E PADRONIZAR CABEÇALHOS (COLUNAS)
        # ============================================================
        df.columns = [clean_header(col) for col in df.columns]
        print(f"  Colunas tratadas: {list(df.columns)}")
        
        # ============================================================
        # 3. LIMPAR VALORES NAS LINHAS (REMOÇÃO DE ACENTOS E ERROS)
        # ============================================================
        # Identifica colunas categóricas (texto)
        colunas_texto = [col for col in df.columns if df[col].dtype == 'object' or df[col].dtype == 'str']
        
        for col in colunas_texto:
            # Substitui nulls na coluna por "Nao Alocado"
            df[col] = df[col].fillna("Nao Alocado")
            # Aplica limpeza textual (mapeamentos + remoção de acentos)
            df[col] = df[col].apply(clean_text_value)
            
        # ============================================================
        # 4. TRATAMENTO DE TIPOS DE DADOS PARA SQL
        # ============================================================
        # Coluna 'ano' deve ser inteiro
        if 'ano' in df.columns:
            df['ano'] = pd.to_numeric(df['ano'], errors='coerce').fillna(0).astype(int)
            
        # Colunas numéricas de valores/emissões devem ser float
        colunas_numericas = [col for col in df.columns if 'emissao' in col or 'valor' in col]
        for col in colunas_numericas:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
            
        # ============================================================
        # 5. ORDENAÇÃO E RETIRADA DE DUPLICATAS
        # ============================================================
        # Remove registros duplicados
        len_antes = len(df)
        df = df.drop_duplicates()
        len_depois = len(df)
        if len_antes != len_depois:
            print(f"  Clean: Removidos {len_antes - len_depois} registros duplicados.")
            
        # Ordenação consistente (Ano e coluna categórica principal)
        sort_cols = []
        if 'ano' in df.columns:
            sort_cols.append('ano')
        # Adiciona a primeira coluna de texto se houver
        if colunas_texto:
            sort_cols.append(colunas_texto[0])
            
        if sort_cols:
            df = df.sort_values(sort_cols).reset_index(drop=True)
            
        # ============================================================
        # 6. EXPORTAR PARA CSV EM UTF-8
        # ============================================================
        nome_arquivo = clean_sheet_name(sheet_name)
        caminho_saida = os.path.join(PASTA_DESTINO, nome_arquivo)
        
        # Salva o arquivo CSV com encoding UTF-8 puro (sem BOM)
        df.to_csv(caminho_saida, index=False, encoding='utf-8')
        
        print(f"  CSV Generated: '{nome_arquivo}' ({len(df)} rows)")
        print(f"  Sample of categories: {list(df[colunas_texto[0]].unique()[:5]) if colunas_texto else []}")

    print("\n" + "=" * 60)
    print("PROCESS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == '__main__':
    run_etl()
