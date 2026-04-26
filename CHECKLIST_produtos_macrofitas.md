# Checklist de viabilidade dos produtos

Data da avaliacao: 2026-04-26

## 1) Inventario da pasta

- [x] Dados_geoespacial_baias.txt
- [x] Dados_geoespacial_biomassa.txt
- [x] Geolocalizacao_pontos_coletas.txt
- [x] Lista_completa_macroalgas.txt
- [x] COMPOSICAO E ESTRUTURA ESPACIAL DA COMUNIDADE MACROFITOBENTICA DAS BAIAS DA ILHA DE SANTA CATARINA.pdf

## 2) Produto: mapa interativo (estilo mapa_google_macrofitas.html)

Status: PARCIALMENTE VIAVEL COM ADAPTACAO

Atende:
- [x] Latitude/Longitude por estacao
- [x] Sigla da estacao
- [x] Biomassa media por estacao
- [x] Lista qualitativa de algas por estacao
- [x] Descricao/local da estacao

Pontos de adaptacao obrigatoria:
- [ ] Converter coordenadas DMS para decimal (Leaflet/Google usa decimal)
- [ ] Padronizar separador e encoding (UTF-8)
- [ ] Validar consistencia de estacoes entre arquivos (ex.: ordem PAP/CAI varia)
- [ ] Definir metrica para tamanho/cor dos marcadores (riqueza ou biomassa)

## 3) Produto: cladograma interativo avancado

Status: IMPLEMENTADO LOCALMENTE

Atende:
- [x] Lista de especies por grupo maior (Filo/Classe)
- [x] Nomes de especies para busca/filtro

Complementacoes executadas:
- [x] Hierarquia taxonomica por especie (Filo > Classe > Ordem > Familia > Genero > Especie)
- [x] JSON estruturado enriquecido com um registro por especie
- [x] Normalizacao contextual de abreviacoes de genero (ex.: C. antennina -> Chaetomorpha antennina)
- [x] Enriquecimento taxonomico automatico via GBIF com cache local

## 4) Produto: portal indice (pagina inicial)

Status: IMPLEMENTADO LOCALMENTE

Atende:
- [x] Dados base para estatisticas resumidas
- [x] Dados para linkar para mapa e cladogramas

Pontos de adaptacao:
- [x] Gerar metricas automaticamente a partir do dataset (numero de especies, classes, estacoes)
- [x] Garantir consistencia entre contagens do portal e contagens reais dos dados

## 5) Conclusao objetiva

- [x] E possivel gerar os produtos solicitados com os arquivos existentes.
- [x] Para o mapa: pipeline de conversao de coordenadas e limpeza implementado.
- [x] Para o cladograma avancado: taxonomia enriquecida (ordem/familia/genero) implementada.

## 6) Pipeline recomendado (resumo)

1. Consolidar os TXT em um dataset unico (CSV/JSON).
2. Limpar nomes taxonomicos e corrigir abreviacoes.
3. Converter coordenadas DMS -> decimal.
4. Exportar:
   - pontos_mapa.json
   - especies_taxonomia.json
   - resumo_metricas.json
5. Renderizar paginas HTML (Leaflet + D3) com os JSON gerados.

## 7) Entregaveis minimos para automatizar

- [x] Script de preprocessamento (Python)
- [x] JSON do mapa
- [x] JSON da taxonomia
- [x] HTML do mapa
- [x] HTML do cladograma
- [x] HTML indice

## 8) Produtos gerados

- [x] saida_produtos/pontos_mapa.json
- [x] saida_produtos/especies_taxonomia_base.json
- [x] saida_produtos/especies_taxonomia_enriquecida.json
- [x] saida_produtos/cladograma_hierarquia.json
- [x] saida_produtos/resumo_metricas.json
- [x] site_local/index_local_macrofitas.html
- [x] site_local/mapa_local_macrofitas.html
- [x] site_local/cladograma_local_macrofitas.html
