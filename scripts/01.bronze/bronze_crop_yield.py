import pandas as pd
import os

def process_bronze_crop_yield():
    # Caminhos dos arquivos
    input_file = r'g:\.shortcut-targets-by-id\1LxU2y_h2XY8g0JiAOin2DcmjlXADV8uI\PROJETO_FINAL_GENERATION\data\bronze\crop_yieldKAGGLE.csv\crop_yield.csv'
    output_dir = r'g:\.shortcut-targets-by-id\1LxU2y_h2XY8g0JiAOin2DcmjlXADV8uI\PROJETO_FINAL_GENERATION\data\bronze\kaggle_yield'
    output_file = os.path.join(output_dir, 'crop_yield_bronze.csv')
    
    # Criar diretório se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    print("Iniciando a carga do dataset Agriculture Crop Yield...")
    
    # Lendo o dataset original
    df = pd.read_csv(input_file)
    
    # Selecionando apenas as colunas essenciais para o projeto de Crédito de Carbono e ESG
    colunas_essenciais = [
        'Region',
        'Crop',
        'Soil_Type',
        'Fertilizer_Used',
        'Irrigation_Used',
        'Rainfall_mm',
        'Temperature_Celsius',
        'Yield_tons_per_hectare'
    ]
    
    # Filtro das colunas essenciais
    df_bronze = df[colunas_essenciais].copy()
    
    # Salvando na camada bronze (nesta camada evitamos alterar tipos de dados ou renomear fortemente, apenas filtramos o escopo)
    df_bronze.to_csv(output_file, index=False)
    
    print(f"Sucesso! {len(df_bronze)} registros processados.")
    print(f"Arquivo salvo em: {output_file}")

if __name__ == "__main__":
    process_bronze_crop_yield()
