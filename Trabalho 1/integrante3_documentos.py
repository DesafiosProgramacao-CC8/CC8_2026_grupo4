import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List

from integrante1_varredura import ArquivoEncontrado
from integrante2_arvore_avl import ArvoreAVL


PADRAO_PALAVRA = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_]+", re.UNICODE)


def normalizar_texto(texto: str) -> str:
    texto = texto.casefold()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(caractere for caractere in texto if unicodedata.category(caractere) != "Mn")


def separar_palavras(texto: str):
    return [normalizar_texto(p) for p in PADRAO_PALAVRA.findall(texto) if p.strip()]


@dataclass
class DocumentoIndexado:
    name: str
    path: str
    extension: str
    kind: str
    size_bytes: int
    modified_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    word_index: Any = None
    total_words: int = 0

    @property
    def key(self) -> str:
        return f"{self.name.casefold()}|{self.path.casefold()}"


@dataclass
class ResultadoDocumento:
    record: DocumentoIndexado
    relevance: float
    reason: str


class IndexadorDocumentos:
    """Lê TXT, conta palavras e calcula relevância de documentos."""

    def indexar(self, arquivo: ArquivoEncontrado) -> DocumentoIndexado:
        with open(arquivo.path, "r", encoding="utf-8", errors="ignore") as txt:
            conteudo = txt.read()

        palavras = separar_palavras(conteudo)
        arvore_palavras = ArvoreAVL()

        for palavra in palavras:
            quantidade = arvore_palavras.buscar(palavra)
            arvore_palavras.inserir(palavra, 1 if quantidade is None else quantidade + 1)

        frequencias = list(arvore_palavras.itens())
        frequencias.sort(key=lambda item: (-item[1], item[0]))

        metadados = {
            "extension": arquivo.extension.lstrip("."),
            "size_bytes": arquivo.size_bytes,
            "unique_words": arvore_palavras.tamanho,
            "common_words": frequencias[:10],
        }

        return DocumentoIndexado(
            name=arquivo.name,
            path=arquivo.path,
            extension=arquivo.extension,
            kind="document",
            size_bytes=arquivo.size_bytes,
            modified_at=arquivo.modified_at,
            metadata=metadados,
            word_index=arvore_palavras,
            total_words=len(palavras),
        )

    def alimentar_indice_invertido(self, documento: DocumentoIndexado, indice_conteudo: ArvoreAVL) -> None:
        for palavra, quantidade in documento.word_index.itens():
            ocorrencias = indice_conteudo.buscar(palavra)
            if ocorrencias is None:
                ocorrencias = {}
            ocorrencias[documento.path] = quantidade
            indice_conteudo.inserir(palavra, ocorrencias)

    def buscar(
        self,
        consulta: str,
        indice_documentos: ArvoreAVL,
        indice_conteudo: ArvoreAVL,
        arquivos_por_caminho: dict,
    ) -> List[ResultadoDocumento]:
        consulta_normalizada = normalizar_texto(consulta)
        termos = separar_palavras(consulta)
        caminhos_candidatos = set()

        # Procura primeiro pelo conteúdo usando o índice invertido.
        for termo in termos:
            ocorrencias = indice_conteudo.buscar(termo)
            if ocorrencias:
                caminhos_candidatos.update(ocorrencias.keys())

        # Também permite pesquisar por nome ou caminho do arquivo.
        for documento in indice_documentos.valores():
            nome = normalizar_texto(documento.name)
            caminho = normalizar_texto(documento.path)
            if consulta_normalizada in nome or consulta_normalizada in caminho:
                caminhos_candidatos.add(documento.path)

        resultados = []

        for caminho_documento in caminhos_candidatos:
            documento = arquivos_por_caminho.get(caminho_documento)
            if documento is None or documento.kind != "document":
                continue

            nome = normalizar_texto(documento.name)
            caminho = normalizar_texto(documento.path)
            achou_nome = consulta_normalizada in nome
            achou_caminho = consulta_normalizada in caminho

            ocorrencias_total = 0
            termos_encontrados = 0

            for termo in termos:
                quantidade = documento.word_index.buscar(termo) or 0
                ocorrencias_total += quantidade
                if quantidade > 0:
                    termos_encontrados += 1

            if not (achou_nome or achou_caminho or ocorrencias_total > 0):
                continue

            pontuacao_conteudo = (ocorrencias_total / max(documento.total_words, 1)) * 100.0
            bonus_cobertura = (termos_encontrados / max(len(termos), 1)) * 20.0 if termos else 0.0
            bonus_nome = 25.0 if achou_nome else 0.0
            bonus_caminho = 5.0 if achou_caminho and not achou_nome else 0.0
            relevancia = pontuacao_conteudo + bonus_cobertura + bonus_nome + bonus_caminho

            motivos = []
            if ocorrencias_total:
                motivos.append(f"{ocorrencias_total} ocorrência(s) no conteúdo")
            if achou_nome:
                motivos.append("termo no nome")
            elif achou_caminho:
                motivos.append("termo no caminho")

            resultados.append(
                ResultadoDocumento(
                    record=documento,
                    relevance=round(relevancia, 3),
                    reason=", ".join(motivos),
                )
            )

        return resultados
