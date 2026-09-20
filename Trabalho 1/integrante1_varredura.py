import os
from dataclasses import dataclass
from typing import List, Tuple


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
DOCUMENT_EXTENSIONS = {".txt"}


@dataclass
class ArquivoEncontrado:
    """Informações básicas encontradas durante a varredura da pasta."""

    name: str
    path: str
    extension: str
    kind: str
    size_bytes: int
    modified_at: float


class VarredorPastas:
    """Parte responsável por percorrer a pasta e suas subpastas."""

    def varrer(self, pasta: str) -> Tuple[List[ArquivoEncontrado], List[str]]:
        pasta = os.path.abspath(os.path.expanduser(pasta))

        if not os.path.isdir(pasta):
            raise ValueError("A pasta informada não existe ou não é uma pasta válida.")

        arquivos = []
        ignorados = []

        def erro_varredura(erro):
            ignorados.append(getattr(erro, "filename", str(erro)))

        for raiz, diretorios, nomes_arquivos in os.walk(
            pasta, onerror=erro_varredura
        ):
            # Mantém apenas as subpastas que podem ser lidas.
            diretorios_lidos = []

            for diretorio in diretorios:
                caminho_diretorio = os.path.join(raiz, diretorio)

                if os.access(caminho_diretorio, os.R_OK):
                    diretorios_lidos.append(diretorio)
                else:
                    ignorados.append(caminho_diretorio)

            diretorios[:] = diretorios_lidos

            for nome in nomes_arquivos:
                caminho = os.path.join(raiz, nome)
                extensao = os.path.splitext(nome)[1].casefold()

                if extensao in IMAGE_EXTENSIONS:
                    tipo = "image"
                elif extensao in DOCUMENT_EXTENSIONS:
                    tipo = "document"
                else:
                    continue

                try:
                    if not os.access(caminho, os.R_OK):
                        ignorados.append(caminho)
                        continue

                    dados = os.stat(caminho)

                    arquivos.append(
                        ArquivoEncontrado(
                            name=nome,
                            path=os.path.abspath(caminho),
                            extension=extensao,
                            kind=tipo,
                            size_bytes=dados.st_size,
                            modified_at=dados.st_mtime,
                        )
                    )

                except (OSError, PermissionError) as erro:
                    ignorados.append(f"{caminho} ({erro})")

        return arquivos, ignorados