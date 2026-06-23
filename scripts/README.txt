






	03. OuroO arquivo "cria_camada_gold.py". Cria a camada outro, lê dados de múltiplas fontes da camada Prata, realiza joins, 
agregações e cria o painel ESG consolidado com as tabelas de Star Schema

camada prata ---> Camada Ouro

Camada: Prata → Ouro
Origem dos dados (leitura):
dados/02.prata/nasa/prata_nasa_chuva_estados_brasil.csv
dados/02.prata/mapbiomas/prata_desmatamento_estado_bioma.csv
dados/02.prata/mapbiomas/prata_pastagem.csv
dados/02.prata/SEEG/Limpeza_Padrao_Prata/emissao_por_estado.csv
dados/02.prata/kaggle_crop_yield/crop_yield_silver.csv
(Todos caminhos relativos)
Destino dos dados (escrita):
dados/03.ouro/gold_painel_esg_consolidado.csv
dados/03.ouro/gold_painel_esg_consolidado.parquet
dados/03.ouro/star_schema/dim_estado.csv
dados/03.ouro/star_schema/dim_bioma.csv
dados/03.ouro/star_schema/dim_calendario.csv
dados/03.ouro/star_schema/fato_desmatamento.csv
dados/03.ouro/star_schema/fato_pastagem.csv
dados/03.ouro/star_schema/fato_emissoes.csv
dados/03.ouro/star_schema/fato_clima.csv
dados/03.ouro/star_schema/fato_produtividade_agricola.csv
(Todos caminhos relativos)

Transformações-chave:
Leitura de múltiplas fontes da camada Prata
Padronização de nomes de estados (mapeamento de siglas)
Joins entre datasets via estado + ano
Agregações por estado, bioma e ano
Criação de tabelas dimensão (estado, bioma, calendário) e fato (desmatamento, pastagem, emissões, clima, produtividade)
Exportação em CSV e Parquet