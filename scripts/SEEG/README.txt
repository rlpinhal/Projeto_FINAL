
Arquivo: scripts/SEEG/01_seeg_emissao_total_prata.py
Propósito: Processa os dados brutos do SEEG (Sistema de Estimativas de Emissões e Remoções de Gases de Efeito Estufa) para criar CSVs intermediários da camada Bronze a partir da tabela raw consolidada.
Tipo: ETL
Camada: Raw → Bronze

Origem dos dados (leitura):
dados/00.raw/seeg_all.csv (caminho relativo)

Destino dos dados (escrita):
dados/01.bronze/SEEG/emissao-total.csv
dados/01.bronze/SEEG/emissao-total-por-bioma.csv
dados/01.bronze/SEEG/emissao-total-por-categoria.csv
dados/01.bronze/SEEG/emissoes-totais-por-estado.csv
dados/01.bronze/SEEG/atividade-geral.csv
(Todos caminhos relativos)

Transformações-chave:
Parsing complexo do CSV com separador ; e encoding latin1
Melt/unpivot de colunas de anos para formato vertical
Filtros por nível de agregação (Nível 1-6), tipo de gás (CO2e GWP-AR5)
Agrupamento por bioma, categoria, estado, setor
Renomeação e padronização de colunas