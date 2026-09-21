from dataclasses import dataclass
from typing import Optional

from integrante2_arvore_avl import ArvoreAVL
from integrante3_tipos import criar_tipo, TipoInteiro, TipoData, ErroTipo


class ErroBanco(Exception):
    pass


@dataclass
class Campo:
    nome: str
    tipo_nome: str
    chave_estrangeira: Optional[str] = None

    @property
    def tipo(self):
        return criar_tipo(self.tipo_nome)


class Tabela:
    def __init__(self, nome: str, campos):
        self.nome = nome
        self.campos = [Campo("id", "INTEIRO")] + campos
        self.registros = ArvoreAVL()
        self.proximo_id = 1

    def campo(self, nome: str) -> Campo:
        for campo in self.campos:
            if campo.nome == nome:
                return campo
        raise ErroBanco(f"Campo '{nome}' não existe na tabela '{self.nome}'.")

    @property
    def campos_usuario(self):
        return self.campos[1:]


class BancoDados:
    def __init__(self):
        self.tabelas = {}

    def vazio(self):
        return len(self.tabelas) == 0

    def tabela(self, nome: str) -> Tabela:
        if nome not in self.tabelas:
            raise ErroBanco(f"Tabela '{nome}' não existe.")
        return self.tabelas[nome]

    def criar_tabela(self, nome: str, campos_def):
        if nome in self.tabelas:
            raise ErroBanco(f"A tabela '{nome}' já existe.")
        if not campos_def:
            raise ErroBanco("A tabela deve possuir pelo menos um campo além do id.")

        nomes = set()
        campos = []
        for d in campos_def:
            if d["nome"] == "id":
                raise ErroBanco("O campo id é criado automaticamente e não pode ser informado.")
            if d["nome"] in nomes:
                raise ErroBanco(f"Campo duplicado: {d['nome']}")
            nomes.add(d["nome"])

            fk = d.get("fk")
            if fk:
                if d["tipo"] != "INTEIRO":
                    raise ErroBanco("CHAVESTRANGEIRA só pode ser usada após o tipo INTEIRO.")
                if fk not in self.tabelas:
                    raise ErroBanco(f"Tabela referenciada '{fk}' ainda não existe.")
            campos.append(Campo(d["nome"], d["tipo"], fk))

        self.tabelas[nome] = Tabela(nome, campos)
        return f"Tabela '{nome}' criada."

    def apagar_tabela(self, nome: str):
        tabela = self.tabela(nome)
        if tabela.registros.tamanho > 0:
            raise ErroBanco("Uma tabela só pode ser apagada quando não possui registros.")
        for outra in self.tabelas.values():
            if outra.nome == nome:
                continue
            for campo in outra.campos:
                if campo.chave_estrangeira == nome:
                    raise ErroBanco(f"A tabela '{nome}' é referenciada pela tabela '{outra.nome}'.")
        del self.tabelas[nome]
        return f"Tabela '{nome}' apagada."

    def _converter_token(self, campo: Campo, token):
        if token is None or token.get("valor") is None:
            raise ErroBanco("Valores nulos não são permitidos.")
        try:
            return campo.tipo.converter(token["valor"], token.get("citado", False))
        except ErroTipo as e:
            raise ErroBanco(str(e)) from e

    def _validar_fk(self, campo: Campo, valor):
        if campo.chave_estrangeira:
            tabela_ref = self.tabela(campo.chave_estrangeira)
            if tabela_ref.registros.buscar(valor) is None:
                raise ErroBanco(
                    f"Chave estrangeira inválida: id {valor} não existe em '{campo.chave_estrangeira}'."
                )

    def inserir(self, nome_tabela: str, valores_tokens):
        tabela = self.tabela(nome_tabela)
        if len(valores_tokens) != len(tabela.campos_usuario):
            raise ErroBanco(
                f"Quantidade de valores incorreta. Esperado: {len(tabela.campos_usuario)}."
            )

        registro = {"id": tabela.proximo_id}
        for campo, token in zip(tabela.campos_usuario, valores_tokens):
            valor = self._converter_token(campo, token)
            self._validar_fk(campo, valor)
            registro[campo.nome] = valor

        tabela.registros.inserir(tabela.proximo_id, registro)
        id_inserido = tabela.proximo_id
        tabela.proximo_id += 1
        return f"Registro inserido em '{nome_tabela}' com id {id_inserido}."

    def _resolver_operando(self, tabela: Tabela, registro, token, tipo_preferido=None):
        # Palavra sem aspas que coincide com um campo = referência ao valor do campo.
        if not token.get("citado", False) and token.get("tipo_token") == "PALAVRA":
            nome = token["valor"]
            for campo in tabela.campos:
                if campo.nome == nome:
                    return registro[nome], campo.tipo

        tipo = tipo_preferido
        if tipo is None:
            raise ErroBanco("Não foi possível determinar o tipo do valor.")
        try:
            return tipo.converter(token["valor"], token.get("citado", False)), tipo
        except ErroTipo as e:
            raise ErroBanco(str(e)) from e

    def _avaliar_condicao(self, tabela: Tabela, registro, condicao) -> bool:
        if condicao is None:
            return True
        campo = tabela.campo(condicao["campo"])
        esquerdo = registro[campo.nome]
        direito, _ = self._resolver_operando(tabela, registro, condicao["valor"], campo.tipo)
        try:
            return campo.tipo.comparar(condicao["operador"], esquerdo, direito)
        except ErroTipo as e:
            raise ErroBanco(str(e)) from e

    def _ids_filtrados(self, tabela: Tabela, condicao):
        # Otimização exigida pelo uso da AVL: id == valor faz busca direta.
        if condicao and condicao["campo"] == "id" and condicao["operador"] == "==":
            try:
                valor = TipoInteiro().converter(
                    condicao["valor"]["valor"], condicao["valor"].get("citado", False)
                )
            except ErroTipo as e:
                raise ErroBanco(str(e)) from e
            return [valor] if tabela.registros.buscar(valor) is not None else []

        ids = []
        for chave, registro in tabela.registros.itens():
            if self._avaliar_condicao(tabela, registro, condicao):
                ids.append(chave)
        return ids

    def selecionar(self, nome_tabela: str, condicao=None):
        tabela = self.tabela(nome_tabela)
        resultados = []
        for id_ in self._ids_filtrados(tabela, condicao):
            registro = tabela.registros.buscar(id_)
            if registro is not None:
                resultados.append(dict(registro))
        return resultados

    def _avaliar_expressao(self, tabela: Tabela, registro, campo_destino: Campo, expr):
        op = expr["operador"]
        if op is None:
            valor, _ = self._resolver_operando(tabela, registro, expr["esquerda"], campo_destino.tipo)
            return valor

        esquerdo, tipo_esquerdo = self._resolver_operando(
            tabela, registro, expr["esquerda"], campo_destino.tipo
        )

        # Exceção definida no trabalho: DATA +/- INTEIRO.
        if isinstance(tipo_esquerdo, TipoData) and op in {"+", "-"}:
            try:
                direito = TipoInteiro().converter(
                    expr["direita"]["valor"], expr["direita"].get("citado", False)
                )
            except ErroTipo as e:
                raise ErroBanco(str(e)) from e
        else:
            direito, _ = self._resolver_operando(tabela, registro, expr["direita"], tipo_esquerdo)

        try:
            return tipo_esquerdo.operar(op, esquerdo, direito)
        except ErroTipo as e:
            raise ErroBanco(str(e)) from e

    def atualizar(self, nome_tabela: str, alteracoes, condicao=None):
        tabela = self.tabela(nome_tabela)
        for alt in alteracoes:
            if alt["campo"] == "id":
                raise ErroBanco("O campo id não pode ser modificado.")
            tabela.campo(alt["campo"])

        ids = self._ids_filtrados(tabela, condicao)
        for id_ in ids:
            registro = tabela.registros.buscar(id_)
            novo = dict(registro)
            for alt in alteracoes:
                campo = tabela.campo(alt["campo"])
                valor = self._avaliar_expressao(tabela, novo, campo, alt["expressao"])
                if not campo.tipo.validar_python(valor):
                    raise ErroBanco(f"Resultado incompatível com o tipo {campo.tipo_nome} do campo '{campo.nome}'.")
                self._validar_fk(campo, valor)
                novo[campo.nome] = valor
            tabela.registros.inserir(id_, novo)

        return f"{len(ids)} registro(s) atualizado(s) em '{nome_tabela}'."

    def _referenciado(self, nome_tabela: str, id_: int):
        for tabela in self.tabelas.values():
            for campo in tabela.campos:
                if campo.chave_estrangeira == nome_tabela:
                    for registro in tabela.registros.valores():
                        if registro[campo.nome] == id_:
                            return tabela.nome, campo.nome
        return None

    def apagar_dados(self, nome_tabela: str, condicao=None):
        tabela = self.tabela(nome_tabela)
        ids = self._ids_filtrados(tabela, condicao)
        for id_ in ids:
            ref = self._referenciado(nome_tabela, id_)
            if ref:
                raise ErroBanco(
                    f"O id {id_} de '{nome_tabela}' é referenciado por '{ref[0]}.{ref[1]}' e não pode ser apagado."
                )
        for id_ in ids:
            tabela.registros.remover(id_)
        return f"{len(ids)} registro(s) apagado(s) de '{nome_tabela}'."

    def to_dict(self):
        dados = {"tabelas": {}}
        for nome, tabela in self.tabelas.items():
            dados_tabela = {
                "proximo_id": tabela.proximo_id,
                "campos": [
                    {"nome": c.nome, "tipo": c.tipo_nome, "fk": c.chave_estrangeira}
                    for c in tabela.campos_usuario
                ],
                "registros": [dict(registro) for registro in tabela.registros.valores()],
            }
            dados["tabelas"][nome] = dados_tabela
        return dados

    def carregar_dict(self, dados):
        novas = {}
        for nome, d in dados.get("tabelas", {}).items():
            campos = [Campo(c["nome"], c["tipo"], c.get("fk")) for c in d["campos"]]
            tabela = Tabela(nome, campos)
            tabela.proximo_id = int(d["proximo_id"])
            for registro in d.get("registros", []):
                registro = dict(registro)
                tabela.registros.inserir(int(registro["id"]), registro)
            novas[nome] = tabela
        self.tabelas = novas


class ExecutorBanco:
    COMANDOS_ALTERACAO = {
        "CRIATABELA", "APAGATABELA", "INSERIREM", "ATUALIZATABELA", "APAGADADOSDE"
    }

    def __init__(self, banco: BancoDados):
        self.banco = banco

    def executar(self, comando, ao_alterar=None):
        tipo = comando["tipo"]
        snapshot = self.banco.to_dict() if tipo in self.COMANDOS_ALTERACAO else None

        try:
            if tipo == "CRIATABELA":
                resultado = self.banco.criar_tabela(comando["tabela"], comando["campos"])
            elif tipo == "APAGATABELA":
                resultado = self.banco.apagar_tabela(comando["tabela"])
            elif tipo == "INSERIREM":
                resultado = self.banco.inserir(comando["tabela"], comando["valores"])
            elif tipo == "ATUALIZATABELA":
                resultado = self.banco.atualizar(comando["tabela"], comando["alteracoes"], comando["condicao"])
            elif tipo == "APAGADADOSDE":
                resultado = self.banco.apagar_dados(comando["tabela"], comando["condicao"])
            elif tipo == "MOSTRADADOSDE":
                resultado = self.banco.selecionar(comando["tabela"], comando["condicao"])
            else:
                raise ErroBanco(f"Comando '{tipo}' deve ser tratado pelo módulo de integração.")

            if tipo in self.COMANDOS_ALTERACAO and ao_alterar:
                ao_alterar()
            return resultado
        except Exception:
            if snapshot is not None:
                self.banco.carregar_dict(snapshot)
            raise
