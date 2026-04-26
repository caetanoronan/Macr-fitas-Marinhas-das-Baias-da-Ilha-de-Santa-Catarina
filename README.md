# Macrófitas Marinhas das Baias da Ilha de Santa Catarina

Repositório com os produtos web finais (portal, mapa e dois cladogramas) adaptados para os dados da Buzon, com curadoria taxonômica e estrutura pronta para publicação.

## Objetivo

Disponibilizar visualizações interativas para apoio a ensino, pesquisa e divulgação científica sobre macrófitas marinhas das baias da Ilha de Santa Catarina:

- Portal principal de navegação.
- Mapa interativo das estações de coleta.
- Cladograma interativo avançado.
- Cladograma interativo simples em formato disco (sunburst).

## Estrutura principal

- publicacao_final/index.html
- publicacao_final/mapa_google_macrofitas.html
- publicacao_final/cladograma_interativo_macrofitas_funcional_filtros_zoom_teste_pronto.html
- publicacao_final/cladograma_interativo_melhorado.html
- publicacao_final/data/pontos_mapa.json
- publicacao_final/data/cladograma_hierarquia_publicacao.json
- publicacao_final/data/relatorio_curadoria_taxonomica.json
- gerar_produtos_base.py

## Como executar localmente

1. Gerar/atualizar os dados consolidados:

.venv/Scripts/python.exe gerar_produtos_base.py

2. Iniciar servidor HTTP local na raiz do projeto:

.venv/Scripts/python.exe -m http.server 8000

3. Acessar no navegador:

http://localhost:8000/publicacao_final/index.html

## Produtos

### Portal

Arquivo: publicacao_final/index.html

Funções:
- Navegação central para os produtos.
- Métricas dinâmicas carregadas de JSON.
- Bloco de contexto bibliográfico e glossário.
- Suporte a modo claro/escuro com contraste ajustado.

### Mapa interativo

Arquivo: publicacao_final/mapa_google_macrofitas.html

Funções:
- Visualização geográfica das estações.
- Marcadores com riqueza e detalhes por local.
- Painel lateral com estatísticas e lista de estações.

### Cladograma avançado

Arquivo: publicacao_final/cladograma_interativo_macrofitas_funcional_filtros_zoom_teste_pronto.html

Funções:
- Filtros por filo.
- Busca por táxon.
- Zoom e exportação SVG.
- Cores diferenciadas para filos relevantes (incluindo Ochrophyta e Phaeophyceae).

### Cladograma simples (disco)

Arquivo: publicacao_final/cladograma_interativo_melhorado.html

Funções:
- Visualização hierárquica em sunburst.
- Clique para entrar nos níveis taxonômicos.
- Botão Voltar nível para navegação didática.
- Botão Resetar visualização.

## Pipeline de dados

Script: gerar_produtos_base.py

Saídas principais:
- saida_produtos/pontos_mapa.json
- saida_produtos/especies_taxonomia_enriquecida.json
- saida_produtos/especies_taxonomia_publicacao.json
- saida_produtos/cladograma_hierarquia_publicacao.json
- saida_produtos/relatorio_curadoria_taxonomica.json

## Referência científica principal

Bouzon, Janayna Lehmkuhl.
Composição e Estrutura Espacial da Comunidade Macrofitobêntica de Fundos Consolidados das Baías da Ilha de Santa Catarina (SC): Subsídios para a Avaliação do Impacto da Urbanização. 2005.
f. 77; grafs, tabs.
Orientadora: Dra. Zenilda Bouzon.
Dissertação (Mestrado), Universidade Federal de Santa Catarina, Centro de Ciências Biológicas.
Bibliografia: f. 77.

## Tecnologias

- HTML, CSS, JavaScript
- D3.js
- Plotly
- Leaflet
- Python para pré-processamento de dados

## Publicação no GitHub Pages

Checklist rápido:

1. Subir os arquivos para o repositório.
2. Em Settings > Pages, escolher a branch principal e pasta raiz.
3. Confirmar que publicacao_final/index.html está acessível.
4. Testar os quatro produtos após deploy.
