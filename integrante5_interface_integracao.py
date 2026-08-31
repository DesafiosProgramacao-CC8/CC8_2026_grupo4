import os
from datetime import datetime

from flask import Flask, abort, redirect, render_template, request, send_file, url_for

from integrante1_varredura import VarredorPastas
from integrante2_arvore_avl import ArvoreAVL
from integrante3_documentos import IndexadorDocumentos
from integrante4_imagens import IndexadorImagens


app = Flask(__name__)
app.config["SECRET_KEY"] = "iffagle-academic-project"

varredor = VarredorPastas()
indexador_documentos = IndexadorDocumentos()
indexador_imagens = IndexadorImagens()

indice_documentos = ArvoreAVL()
indice_imagens = ArvoreAVL()
indice_conteudo = ArvoreAVL()
arquivos_por_caminho = {}
itens_ignorados = []
pasta_indexada = ""


def formatar_tamanho(tamanho_bytes: int) -> str:
    tamanho = float(tamanho_bytes)
    for unidade in ["B", "KB", "MB", "GB"]:
        if tamanho < 1024 or unidade == "GB":
            return f"{tamanho:.1f} {unidade}"
        tamanho /= 1024


def formatar_data(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")


app.jinja_env.filters["filesize"] = formatar_tamanho
app.jinja_env.filters["datetime"] = formatar_data


def limpar_indices():
    global pasta_indexada
    indice_documentos.limpar()
    indice_imagens.limpar()
    indice_conteudo.limpar()
    arquivos_por_caminho.clear()
    itens_ignorados.clear()
    pasta_indexada = ""


def indexar_pasta(pasta: str):
    global pasta_indexada
    limpar_indices()

    arquivos, ignorados = varredor.varrer(pasta)
    pasta_indexada = os.path.abspath(os.path.expanduser(pasta))
    itens_ignorados.extend(ignorados)

    for arquivo in arquivos:
        try:
            if arquivo.kind == "document":
                documento = indexador_documentos.indexar(arquivo)
                indice_documentos.inserir(documento.key, documento)
                indexador_documentos.alimentar_indice_invertido(documento, indice_conteudo)
                arquivos_por_caminho[documento.path] = documento
            else:
                imagem = indexador_imagens.indexar(arquivo)
                indice_imagens.inserir(imagem.key, imagem)
                arquivos_por_caminho[imagem.path] = imagem
        except (OSError, PermissionError, UnicodeError, ValueError) as erro:
            itens_ignorados.append(f"{arquivo.path} ({erro})")

    return {
        "folder": pasta_indexada,
        "images": indice_imagens.tamanho,
        "documents": indice_documentos.tamanho,
        "skipped": len(itens_ignorados),
    }


def pesquisar(consulta: str, tipo: str):
    resultados = []

    if tipo in ("all", "document"):
        resultados.extend(
            indexador_documentos.buscar(
                consulta,
                indice_documentos,
                indice_conteudo,
                arquivos_por_caminho,
            )
        )

    if tipo in ("all", "image"):
        resultados.extend(indexador_imagens.buscar(consulta, indice_imagens))

    resultados.sort(key=lambda item: (-item.relevance, item.record.name.casefold()))
    return resultados


@app.route("/", methods=["GET", "POST"])
def home():
    mensagem = None
    erro = None
    estatisticas = None

    if request.method == "POST":
        pasta = request.form.get("folder", "").strip()
        try:
            estatisticas = indexar_pasta(pasta)
            mensagem = (
                f"Indexação concluída: {estatisticas['documents']} documento(s), "
                f"{estatisticas['images']} imagem(ns) e "
                f"{estatisticas['skipped']} item(ns) ignorado(s)."
            )
        except ValueError as excecao:
            erro = str(excecao)

    return render_template(
        "index.html",
        indexed_folder=pasta_indexada,
        message=mensagem,
        error=erro,
        stats=estatisticas,
    )


@app.get("/search")
def search():
    consulta = request.args.get("q", "").strip()
    tipo = request.args.get("kind", "all")

    if tipo not in {"all", "document", "image"}:
        tipo = "all"

    resultados = pesquisar(consulta, tipo) if consulta else []

    return render_template(
        "results.html",
        query=consulta,
        kind=tipo,
        results=resultados,
        indexed_folder=pasta_indexada,
    )


@app.get("/open")
def open_file():
    caminho = os.path.abspath(request.args.get("path", ""))
    arquivo = arquivos_por_caminho.get(caminho)

    if arquivo is None or not os.path.isfile(arquivo.path):
        abort(404)

    return send_file(arquivo.path, as_attachment=False)


@app.get("/reset")
def reset():
    limpar_indices()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
