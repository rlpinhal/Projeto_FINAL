# 🌾 Ecossistema de Inteligência Agroambiental e Créditos de Carbono

Bem-vindo ao repositório central do projeto de Monitoramento e Análise de Dados Agroambientais. Este sistema cruza variáveis climáticas, uso da terra e índices de poluentes para viabilizar a auditoria e validação de reduções de Gases de Efeito Estufa (GEE) voltadas ao mercado de Créditos de Carbono e conformidade ESG.

---

## 📁 Arquitetura de Pastas e Diretórios

Para garantir a reprodutibilidade, governança e integridade das transformações de dados (da ingestão ao dashboard), o projeto adota a seguinte estrutura de diretórios:

text
├── .gitignore               # Bloqueio de arquivos pesados, credenciais 
├── README.md                # Este guia principal do repositório
├── requirements.txt         # Dependências do projeto (com versões fixadas)
│
│
├── apoio/                   # Material auxiliar como estudos e exemplos
│   ├── 01.links/               # Links de acesso kanban e fontes 
│   ├── 02.guias/               # Guias de extração para as fontes
│   ├── 03.estudos/             # Aulas e resumos sobre o tema
│   └── ETL_Estatystics_Hotel.ipynb     # Notebook exemplo para extração e limpeza inicial   
│
│
├── dados/                   # Camadas de Armazenamento de Dados (Local)
│   ├── 01_bronze/           # Dados brutos imutáveis (INMET, MapBiomas, Kaggle)
│   ├── 02_prata/            # Dados limpos, tipados e tratados (Prontos para EDA)
│   └── 03_ouro/             # Visões agregadas e tabelas de KPIs finais (Dashboard)
│    
│
├── docs/                    # Documentação Detalhada do Projeto (Markdown)
│   ├── 00.relatorios        # Entregas individuais relatando o trabalho
│   ├── 01.escopo_e_negocio.md # Consolidação do TAP, BRD e Glossário do Domínio
│   ├── 02.fontes_de_dados.md   # Catálogo de APIs e Inventário de Dados Brutos
│   └── 03._____              # Detalhamento da infraestrutura e modelagem
│
│
├── notebooks/               # Análises Exploratórias e Sandbox
│   ├── eda_uso_terra_mapbiomas.ipynb   # Exemplo de arquivo notebook colab
│      
│
├── scripts/                 # Código Fonte Estruturado (Scripts de Produção)
│   ├── __init__.py          # Exemplos
│   ├── ingestao.py          # Scripts de consumo das APIs e pipelines raw->bronze
│   ├── tratamento.py        # Processamento e transformações bronze->silver
│   └── agregacao.py         # Regras de negócio e KPIs silver->gold
│
└── app/                     # Entrega Visual / Data App
   └── dashboard.py         # Aplicação Streamlit, Dash ou código do PoweBI


##  Governança de Inteligência Artificial e Co-Pilotos de Código

Este projeto adotou uma abordagem moderna de desenvolvimento assistido por Inteligência Artificial. Foram utilizadas ferramentas de LLM como **Google Gemini** e **Claude Opus** (via interface integrada de desenvolvimento/Antigravity) operando como co-pilotos consultivos ao longo de todo o ciclo do projeto.

### 🛠️ Escopo de Atuação e Casos de Uso

Os modelos de IA foram integrados estrategicamente nas seguintes frentes:

1. **Diagnóstico Estrutural de Código:** * Análise automatizada de scripts legados para identificação de gargalos de I/O e bugs latentes.
   * Fornecimento de insights valiosos e recomendações arquiteturais para a estruturação das pastas do repositório (`/notebooks`, `/src`, `/data`) e organização das fases da Arquitetura Medalhão.

2. **Correção de Sintaxe e Refatoração Lógica:**
   * Correção ativa de erros de sintaxe e inconsistências de tipos no tratamento de dados utilizando `pandas`.
   * Apoio na estruturação lógica de funções complexas e tratamento de exceções.

3. **Engenharia de Caminhos Resilientes (Mapeamento Dinâmico):**
   * **Problema:** Riscos de quebra do pipeline causados por caminhos rígidos (*hardcoded*) vinculados à montagem do cache de diferentes contas do Google Drive no ambiente Colab (falhas de `os.path.exists()`).
   * **Solução assistida por IA:** Implementação de algoritmos de varredura dinâmica e busca recursiva na árvore de diretórios. Isso garantiu que os notebooks fossem resilientes e independentes do usuário que os estivesse executando.

### 📊 Matriz de Ferramentas Utilizadas

| Ferramenta / Modelo | Principal Função no Projeto | Etapa Aplicada |
| :--- | :--- | :--- |
| **Google Gemini** | Insights de modelagem de dados, geração de padrões de documentação técnica, e estruturação analítica de métricas ESG. | Design de Negócio, Modelagem Gold e Documentação. |
| **Claude Opus** | Debugging complexo de lógica, refatoração de código do pipeline e criação do script de varredura dinâmica de diretórios. | Engenharia (Bronze ➔ Silver) e Code Review. |

---
*Nota: Todas as sugestões, códigos e transformações propostas pelas ferramentas de IA passaram por validação humana, testes locais de integridade e aprovação técnica dos integrantes do grupo antes de serem integradas ao repositório final.*