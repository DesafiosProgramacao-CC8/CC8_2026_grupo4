from dataclasses import dataclass, field
from typing import Any, Dict, List

from PIL import Image

from integrante1_varredura import ArquivoEncontrado
from integrante2_arvore_avl import ArvoreAVL
from integrante3_documentos import normalizar_texto, separar_palavras


@dataclass
class ImagemIndexada:
    name: str
    path: str
    extension: str
    kind: str
    size_bytes: int
    modified_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.name.casefold()}|{self.path.casefold()}"


@dataclass
class ResultadoImagem:
    record: ImagemIndexada
    relevance: float
    reason: str


class IndexadorImagens:
    """Extrai metadados de JPG/PNG e faz a pesquisa das imagens."""

    def indexar(self, arquivo: ArquivoEncontrado) -> ImagemIndexada:
        metadados = {
            "extension": arquivo.extension.lstrip("."),
            "size_bytes": arquivo.size_bytes,
        }

        try:
            with Image.open(arquivo.path) as imagem:
                metadados.update(
                    {
                        "width": imagem.width,
                        "height": imagem.height,
                        "format": imagem.format or arquivo.extension.lstrip(".").upper(),
                        "mode": imagem.mode,
                    }
                )
        except Exception:
            # Uma imagem corrompida não encerra a indexação da pasta.
            metadados.update(
                {
                    "width": None,
                    "height": None,
                    "format": arquivo.extension.lstrip(".").upper(),
                    "mode": "?",
                }
            )

        return ImagemIndexada(
            name=arquivo.name,
            path=arquivo.path,
            extension=arquivo.extension,
            kind="image",
            size_bytes=arquivo.size_bytes,
            modified_at=arquivo.modified_at,
            metadata=metadados,
        )

    def buscar(self, consulta: str, indice_imagens: ArvoreAVL) -> List[ResultadoImagem]:
        consulta_normalizada = normalizar_texto(consulta)
        termos = separar_palavras(consulta)
        resultados = []

        for imagem in indice_imagens.valores():
            campos = [
                normalizar_texto(imagem.name),
                normalizar_texto(imagem.path),
                normalizar_texto(imagem.extension.lstrip(".")),
                normalizar_texto(str(imagem.metadata.get("format", ""))),
                normalizar_texto(str(imagem.metadata.get("mode", ""))),
                str(imagem.metadata.get("width", "")),
                str(imagem.metadata.get("height", "")),
            ]
            texto_pesquisavel = " ".join(campos)

            if consulta_normalizada not in texto_pesquisavel and not all(
                termo in texto_pesquisavel for termo in termos
            ):
                continue

            pontuacao = 0.0
            motivos = []

            if consulta_normalizada in campos[0]:
                pontuacao += 100
                motivos.append("termo no nome")

            if consulta_normalizada in campos[2] or consulta_normalizada in campos[3]:
                pontuacao += 40
                motivos.append("tipo/formato")

            termos_encontrados = sum(1 for termo in termos if termo in texto_pesquisavel)
            pontuacao += termos_encontrados * 10

            if not motivos:
                motivos.append("metadados compatíveis")

            resultados.append(
                ResultadoImagem(
                    record=imagem,
                    relevance=pontuacao,
                    reason=", ".join(motivos),
                )
            )

        return resultados
