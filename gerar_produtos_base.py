from __future__ import annotations

import csv
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "saida_produtos"
CACHE_GBIF = OUT_DIR / "cache_gbif_match.json"

ARQ_BAIAS = BASE_DIR / "Dados_geoespacial_baias.txt"
ARQ_BIOMASSA = BASE_DIR / "Dados_geoespacial_biomassa.txt"
ARQ_GEO = BASE_DIR / "Geolocalizacao_pontos_coletas.txt"
ARQ_LISTA = BASE_DIR / "Lista_completa_macroalgas.txt"


def ler_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normalizar_sigla(sigla: str) -> str:
    return (sigla or "").strip().upper()


def dms_para_decimal(valor: str, eixo: str) -> Optional[float]:
    """Converte coordenada DMS para decimal.

    Aceita formatos como:
    - 27°20'00"S
    - 27∘20′00′′
    """
    if not valor:
        return None

    texto = valor.strip()
    direcao = None

    m_dir = re.search(r"([NSEW])$", texto, flags=re.IGNORECASE)
    if m_dir:
        direcao = m_dir.group(1).upper()
        texto = texto[:-1].strip()

    nums = re.findall(r"\d+(?:\.\d+)?", texto)
    if not nums:
        return None

    graus = float(nums[0])
    minutos = float(nums[1]) if len(nums) > 1 else 0.0
    segundos = float(nums[2]) if len(nums) > 2 else 0.0

    decimal = graus + minutos / 60.0 + segundos / 3600.0

    if direcao:
        if direcao in {"S", "W"}:
            decimal = -abs(decimal)
        else:
            decimal = abs(decimal)
    else:
        if eixo.upper() in {"LAT", "LON"}:
            decimal = -abs(decimal)

    return round(decimal, 7)


def dividir_lista_algas(valor: str) -> List[str]:
    if not valor:
        return []
    itens = [p.strip() for p in valor.split(";")]
    return [i for i in itens if i]


def limpar_rotulo_taxonomico(valor: str) -> str:
    texto = (valor or "").strip()
    texto = re.sub(r"\s*\+\d+\s*$", "", texto)
    texto = texto.rstrip(".")
    return texto


def parse_grupo_filo_classe(campo: str) -> Tuple[str, Optional[str]]:
    texto = (campo or "").strip()
    if "(" in texto and ")" in texto:
        filo = texto.split("(", 1)[0].strip()
        classe = texto.split("(", 1)[1].rsplit(")", 1)[0].strip()
        return filo, classe
    return texto, None


def parse_especie_nome(nome: str) -> Tuple[str, Optional[str]]:
    nome_limpo = limpar_rotulo_taxonomico(nome)
    partes = nome_limpo.split()
    if not partes:
        return nome_limpo, None
    genero = partes[0]
    epiteto = " ".join(partes[1:]) if len(partes) > 1 else None
    return genero, epiteto


def genero_abreviado(genero: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]\.", genero or ""))


def normalizar_nome_especie_contextual(nome: str, ultimo_genero_por_inicial: Dict[str, str]) -> Tuple[str, str, Optional[str], bool]:
    """Expande genero abreviado usando contexto da propria lista taxonomica.

    Exemplo: "C. gracilis" apos "Chaetomorpha aerea" -> "Chaetomorpha gracilis".
    """
    nome_limpo = limpar_rotulo_taxonomico(nome)
    partes = nome_limpo.split()
    if not partes:
        return nome_limpo, "", None, False

    genero = partes[0]
    epiteto = " ".join(partes[1:]) if len(partes) > 1 else None

    if genero_abreviado(genero):
        inicial = genero[0]
        genero_expandido = ultimo_genero_por_inicial.get(inicial)
        if genero_expandido:
            nome_normalizado = f"{genero_expandido} {epiteto}".strip()
            return nome_normalizado, genero_expandido, epiteto, True
        return nome_limpo, genero, epiteto, False

    if genero and genero[0].isalpha() and genero[0].isupper():
        ultimo_genero_por_inicial[genero[0]] = genero

    return nome_limpo, genero, epiteto, False


def carregar_cache_gbif() -> Dict[str, Dict[str, object]]:
    if not CACHE_GBIF.exists():
        return {}
    with CACHE_GBIF.open("r", encoding="utf-8") as f:
        return json.load(f)


def salvar_cache_gbif(cache: Dict[str, Dict[str, object]]) -> None:
    CACHE_GBIF.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_GBIF.open("w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def gbif_match(nome: str, cache: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    chave = (nome or "").strip().lower()
    if not chave:
        return {}
    if chave in cache:
        return cache[chave]

    url = "https://api.gbif.org/v1/species/match?name=" + urllib.parse.quote(nome.strip())
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        data = {}

    cache[chave] = data
    return data


def consolidar_estacoes() -> Dict[str, Dict[str, object]]:
    baias = ler_csv(ARQ_BAIAS)
    biomassa = ler_csv(ARQ_BIOMASSA)
    geo = ler_csv(ARQ_GEO)

    por_sigla: Dict[str, Dict[str, object]] = {}

    for row in baias:
        sigla = normalizar_sigla(row.get("Sigla", ""))
        lat = dms_para_decimal(row.get("Latitude", ""), eixo="LAT")
        lon = dms_para_decimal(row.get("Longitude", ""), eixo="LON")
        algas = dividir_lista_algas(row.get("Lista_Qualitativa_Algas", ""))

        por_sigla[sigla] = {
            "estacao": int(row.get("Estacao", "0") or 0),
            "sigla": sigla,
            "latitude": lat,
            "longitude": lon,
            "biomassa_media_gm2": float(row.get("Biomassa_Media_gm2", "0") or 0),
            "riqueza_taxons": int(float(row.get("Riqueza_Taxons", "0") or 0)),
            "lista_qualitativa_algas": algas,
            "total_algas_lista": len(algas),
        }

    for row in biomassa:
        sigla = normalizar_sigla(row.get("Sigla", ""))
        if not sigla:
            continue
        base = por_sigla.setdefault(sigla, {"sigla": sigla})
        base["descricao_local"] = (row.get("Descricao_Local", "") or "").strip()
        base["principais_algas"] = [
            x.strip()
            for x in (row.get("Principais_Algas", "") or "").split(",")
            if x.strip()
        ]
        if "biomassa_media_gm2" not in base:
            base["biomassa_media_gm2"] = float(row.get("Biomassa_Media_gm2", "0") or 0)

    for row in geo:
        sigla = normalizar_sigla(row.get("Sigla", ""))
        if not sigla:
            continue
        base = por_sigla.setdefault(sigla, {"sigla": sigla})
        lat_txt = row.get("Latitude (S)", "")
        lon_txt = row.get("Longitude (W)", "")
        base["localizacao"] = (row.get("Localizacao", "") or row.get("Localização", "")).strip()
        if base.get("latitude") is None:
            base["latitude"] = dms_para_decimal(lat_txt, eixo="LAT")
        if base.get("longitude") is None:
            base["longitude"] = dms_para_decimal(lon_txt, eixo="LON")

    return por_sigla


def gerar_taxonomia_base() -> Dict[str, object]:
    linhas = ler_csv(ARQ_LISTA)
    grupos = []
    especies_flat = []

    for row in linhas:
        campo_grupo = row.get("Filo / Classe", "")
        lista = row.get("Espécies Identificadas", "") or row.get("Especies Identificadas", "")
        filo, classe = parse_grupo_filo_classe(campo_grupo)

        especies = []
        ultimo_genero_por_inicial: Dict[str, str] = {}
        for item in lista.split(","):
            nome = limpar_rotulo_taxonomico(item)
            if not nome:
                continue
            nome_normalizado, genero_normalizado, epiteto, expandido_por_contexto = normalizar_nome_especie_contextual(
                nome,
                ultimo_genero_por_inicial,
            )
            genero, _ = parse_especie_nome(nome)
            registro = {
                "nome": nome,
                "nome_normalizado": nome_normalizado,
                "genero": genero,
                "genero_normalizado": genero_normalizado,
                "epiteto": epiteto,
                "filo": filo,
                "classe_rotulo": classe,
                "expandido_por_contexto": expandido_por_contexto,
            }
            especies.append(registro)
            especies_flat.append(registro)

        grupos.append(
            {
                "filo": filo,
                "classe_rotulo": classe,
                "quantidade_especies": len(especies),
                "especies": especies,
            }
        )

    return {
        "grupos": grupos,
        "total_especies_registradas": len(especies_flat),
        "especies": especies_flat,
    }


def enriquecer_taxonomia(taxonomia_base: Dict[str, object]) -> Dict[str, object]:
    cache = carregar_cache_gbif()
    grupos_saida = []
    especies_enriquecidas = []

    for grupo in taxonomia_base.get("grupos", []):
        filo_base = (grupo.get("filo") or "Indefinido").strip()
        classe_rotulo = grupo.get("classe_rotulo")
        especies_grupo = []

        for esp in grupo.get("especies", []):
            nome_normalizado = (esp.get("nome_normalizado") or esp.get("nome") or "").strip()
            resposta = gbif_match(nome_normalizado, cache)

            classe_tax = (resposta.get("class") or classe_rotulo or "Classe nao definida").strip()
            ordem_tax = (resposta.get("order") or "Ordem nao definida").strip()
            familia_tax = (resposta.get("family") or "Familia nao definida").strip()
            filo_tax = (resposta.get("phylum") or filo_base or "Filo nao definido").strip()
            genero_tax = (
                resposta.get("genus")
                or esp.get("genero_normalizado")
                or esp.get("genero")
                or "Genero nao definido"
            ).strip()

            enriquecida = {
                **esp,
                "filo": filo_tax,
                "classe_taxonomica": classe_tax,
                "ordem": ordem_tax,
                "familia": familia_tax,
                "genero_normalizado": genero_tax,
                "especie": nome_normalizado,
                "gbif_match_type": resposta.get("matchType"),
                "gbif_status": resposta.get("status"),
                "gbif_confidence": resposta.get("confidence"),
                "gbif_canonical_name": resposta.get("canonicalName"),
                "gbif_scientific_name": resposta.get("scientificName"),
                "taxonomia_fonte": "GBIF" if resposta else "base_local",
            }
            especies_grupo.append(enriquecida)
            especies_enriquecidas.append(enriquecida)

        grupos_saida.append(
            {
                "filo": filo_base,
                "classe_rotulo": classe_rotulo,
                "quantidade_especies": len(especies_grupo),
                "especies": especies_grupo,
            }
        )

    salvar_cache_gbif(cache)

    return {
        "grupos": grupos_saida,
        "total_especies_registradas": len(especies_enriquecidas),
        "especies": especies_enriquecidas,
    }


def _tem_taxonomia_completa(registro: Dict[str, object]) -> bool:
    ordem = (registro.get("ordem") or "").strip().lower()
    familia = (registro.get("familia") or "").strip().lower()
    return ordem not in {"", "ordem nao definida"} and familia not in {"", "familia nao definida"}


def _eh_indeterminado(registro: Dict[str, object]) -> bool:
    epiteto = (registro.get("epiteto") or "").strip().lower().rstrip(".")
    return epiteto in {"sp", "spp", "sp1", "sp2"}


def _normalizar_nome_publicacao(registro: Dict[str, object]) -> str:
    """Escolhe o melhor nome para publicacao usando validacao adicional de match fuzzy."""
    nome_atual = (registro.get("especie") or registro.get("nome_normalizado") or registro.get("nome") or "").strip()
    canonical = (registro.get("gbif_canonical_name") or "").strip()
    match_type = (registro.get("gbif_match_type") or "").strip().upper()
    confidence = int(registro.get("gbif_confidence") or 0)
    status = (registro.get("gbif_status") or "").strip().upper()

    if _eh_indeterminado(registro):
        return nome_atual

    # Regra de curadoria automatica: para fuzzy aceito com boa confianca,
    # preferimos o nome canonico retornado pelo backbone taxonomico.
    if canonical and status == "ACCEPTED" and match_type == "FUZZY" and confidence >= 80:
        return canonical

    if canonical and status == "ACCEPTED" and match_type == "EXACT" and confidence >= 95:
        return canonical

    return nome_atual


def curar_taxonomia_publicacao(taxonomia_enriquecida: Dict[str, object]) -> Tuple[Dict[str, object], Dict[str, object]]:
    especies_curadas: List[Dict[str, object]] = []

    for esp in taxonomia_enriquecida.get("especies", []):
        nome_publicacao = _normalizar_nome_publicacao(esp)
        genero_pub, epiteto_pub = parse_especie_nome(nome_publicacao)

        match_type = (esp.get("gbif_match_type") or "").strip().upper()
        confidence = int(esp.get("gbif_confidence") or 0)
        status = (esp.get("gbif_status") or "").strip().upper()

        pendencias: List[str] = []
        nivel_validacao = "aprovado"

        if _eh_indeterminado(esp):
            nivel_validacao = "revisar"
            pendencias.append("epiteto_indeterminado")

        if not _tem_taxonomia_completa(esp):
            if nivel_validacao == "aprovado":
                nivel_validacao = "revisar"
            pendencias.append("taxonomia_incompleta")

        if match_type == "NONE" or confidence < 80:
            nivel_validacao = "revisar"
            pendencias.append("match_fraco")
        elif match_type == "FUZZY" and confidence < 90:
            if nivel_validacao == "aprovado":
                nivel_validacao = "revisar"
            pendencias.append("fuzzy_conf_baixa")

        if status not in {"", "ACCEPTED"}:
            if nivel_validacao == "aprovado":
                nivel_validacao = "revisar"
            pendencias.append("status_nao_aceito")

        curada = {
            **esp,
            "especie_publicacao": nome_publicacao,
            "genero_publicacao": genero_pub,
            "epiteto_publicacao": epiteto_pub,
            "validacao_taxonomica": nivel_validacao,
            "pendencias_validacao": pendencias,
        }
        especies_curadas.append(curada)

    grupos_map: Dict[str, Dict[str, object]] = {}
    for esp in especies_curadas:
        filo = (esp.get("filo") or "Filo nao definido").strip()
        base = grupos_map.setdefault(
            filo,
            {
                "filo": filo,
                "classe_rotulo": None,
                "quantidade_especies": 0,
                "especies": [],
            },
        )
        base["especies"].append(esp)
        base["quantidade_especies"] += 1

    aprovados = [e for e in especies_curadas if e.get("validacao_taxonomica") == "aprovado"]
    revisar = [e for e in especies_curadas if e.get("validacao_taxonomica") == "revisar"]

    pendencias_unicas: Set[str] = set()
    for esp in revisar:
        for p in esp.get("pendencias_validacao", []):
            pendencias_unicas.add(str(p))

    relatorio = {
        "total_especies": len(especies_curadas),
        "aprovadas": len(aprovados),
        "revisar": len(revisar),
        "percentual_aprovadas": round((len(aprovados) / len(especies_curadas)) * 100, 2) if especies_curadas else 0,
        "tipos_pendencia": sorted(pendencias_unicas),
        "casos_revisar": [
            {
                "nome_original": esp.get("nome"),
                "nome_publicacao": esp.get("especie_publicacao"),
                "match": esp.get("gbif_match_type"),
                "confidence": esp.get("gbif_confidence"),
                "pendencias": esp.get("pendencias_validacao"),
            }
            for esp in revisar
        ],
    }

    saida = {
        "grupos": sorted(grupos_map.values(), key=lambda g: str(g.get("filo", ""))),
        "total_especies_registradas": len(especies_curadas),
        "especies": especies_curadas,
    }

    return saida, relatorio


def _get_or_create_child(no: Dict[str, object], nome: str) -> Dict[str, object]:
    filhos = no.setdefault("children", [])
    for filho in filhos:
        if filho.get("name") == nome:
            return filho
    novo = {"name": nome, "children": []}
    filhos.append(novo)
    return novo


def gerar_hierarquia_cladograma(taxonomia_enriquecida: Dict[str, object]) -> Dict[str, object]:
    raiz = {"name": "Macrofitas ISC", "children": []}

    for esp in taxonomia_enriquecida.get("especies", []):
        filo = (esp.get("filo") or "Filo nao definido").strip()
        classe = (esp.get("classe_taxonomica") or esp.get("classe_rotulo") or "Classe nao definida").strip()
        ordem = (esp.get("ordem") or "Ordem nao definida").strip()
        familia = (esp.get("familia") or "Familia nao definida").strip()
        genero = (esp.get("genero_normalizado") or "Genero nao definido").strip()
        especie = (esp.get("especie") or esp.get("nome") or "Especie nao definida").strip()

        no_filo = _get_or_create_child(raiz, filo)
        no_classe = _get_or_create_child(no_filo, classe)
        no_ordem = _get_or_create_child(no_classe, ordem)
        no_familia = _get_or_create_child(no_ordem, familia)
        no_genero = _get_or_create_child(no_familia, genero)
        _get_or_create_child(no_genero, especie)

    return raiz


def gerar_hierarquia_cladograma_publicacao(taxonomia_publicacao: Dict[str, object]) -> Dict[str, object]:
    raiz = {"name": "Macrofitas ISC", "children": []}

    for esp in taxonomia_publicacao.get("especies", []):
        filo = (esp.get("filo") or "Filo nao definido").strip()
        classe = (esp.get("classe_taxonomica") or esp.get("classe_rotulo") or "Classe nao definida").strip()
        ordem = (esp.get("ordem") or "Ordem nao definida").strip()
        familia = (esp.get("familia") or "Familia nao definida").strip()
        genero = (esp.get("genero_publicacao") or esp.get("genero_normalizado") or "Genero nao definido").strip()
        especie = (esp.get("especie_publicacao") or esp.get("especie") or esp.get("nome") or "Especie nao definida").strip()

        no_filo = _get_or_create_child(raiz, filo)
        no_classe = _get_or_create_child(no_filo, classe)
        no_ordem = _get_or_create_child(no_classe, ordem)
        no_familia = _get_or_create_child(no_ordem, familia)
        no_genero = _get_or_create_child(no_familia, genero)
        _get_or_create_child(no_genero, especie)

    return raiz


def gerar_resumo_metricas(estacoes: Dict[str, Dict[str, object]], taxonomia: Dict[str, object]) -> Dict[str, object]:
    lista_estacoes = list(estacoes.values())
    total_estacoes = len(lista_estacoes)

    biomassa_vals = [float(e.get("biomassa_media_gm2", 0) or 0) for e in lista_estacoes]
    riqueza_vals = [int(e.get("riqueza_taxons", 0) or 0) for e in lista_estacoes]

    return {
        "total_estacoes": total_estacoes,
        "total_especies_taxonomia_base": int(taxonomia.get("total_especies_registradas", 0) or 0),
        "biomassa_media_geral_gm2": round(sum(biomassa_vals) / total_estacoes, 2) if total_estacoes else 0,
        "biomassa_maxima_gm2": max(biomassa_vals) if biomassa_vals else 0,
        "riqueza_media_por_estacao": round(sum(riqueza_vals) / total_estacoes, 2) if total_estacoes else 0,
        "riqueza_maxima_estacao": max(riqueza_vals) if riqueza_vals else 0,
        "observacao": "Taxonomia enriquecida disponivel em especies_taxonomia_enriquecida.json e cladograma_hierarquia.json.",
    }


def salvar_json(path: Path, dados: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def main() -> None:
    estacoes = consolidar_estacoes()
    taxonomia_base = gerar_taxonomia_base()
    taxonomia_enriquecida = enriquecer_taxonomia(taxonomia_base)
    hierarquia_cladograma = gerar_hierarquia_cladograma(taxonomia_enriquecida)
    taxonomia_publicacao, relatorio_curadoria = curar_taxonomia_publicacao(taxonomia_enriquecida)
    hierarquia_publicacao = gerar_hierarquia_cladograma_publicacao(taxonomia_publicacao)
    resumo = gerar_resumo_metricas(estacoes, taxonomia_enriquecida)

    lista_estacoes = sorted(estacoes.values(), key=lambda x: int(x.get("estacao", 10**9)))

    salvar_json(OUT_DIR / "pontos_mapa.json", lista_estacoes)
    salvar_json(OUT_DIR / "especies_taxonomia_base.json", taxonomia_base)
    salvar_json(OUT_DIR / "especies_taxonomia_enriquecida.json", taxonomia_enriquecida)
    salvar_json(OUT_DIR / "cladograma_hierarquia.json", hierarquia_cladograma)
    salvar_json(OUT_DIR / "especies_taxonomia_publicacao.json", taxonomia_publicacao)
    salvar_json(OUT_DIR / "cladograma_hierarquia_publicacao.json", hierarquia_publicacao)
    salvar_json(OUT_DIR / "relatorio_curadoria_taxonomica.json", relatorio_curadoria)
    salvar_json(OUT_DIR / "resumo_metricas.json", resumo)

    print("Arquivos gerados em:", OUT_DIR)
    print("- pontos_mapa.json")
    print("- especies_taxonomia_base.json")
    print("- especies_taxonomia_enriquecida.json")
    print("- cladograma_hierarquia.json")
    print("- especies_taxonomia_publicacao.json")
    print("- cladograma_hierarquia_publicacao.json")
    print("- relatorio_curadoria_taxonomica.json")
    print("- resumo_metricas.json")


if __name__ == "__main__":
    main()
