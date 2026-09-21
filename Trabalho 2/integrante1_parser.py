"""Integrante 1 - Leitura e interpretação dos comandos IFFARQL.

Mantido propositalmente simples: transforma uma linha digitada em um dicionário
que o executor do banco consegue processar.
"""

from dataclasses import dataclass
import re
from typing import List


class ErroSintaxe(Exception):
    pass


@dataclass
class Token:
    valor: str
    tipo: str  # PALAVRA, NUMERO, TEXTO, OPERADOR, SIMBOLO


COMANDOS = {
    "CRIATABELA", "APAGATABELA", "INSERIREM", "ATUALIZATABELA",
    "APAGADADOSDE", "MOSTRADADOSDE", "SALVARBD", "CARREGARBD",
    "CARREGARIFFARQL",
}

TIPOS = {"INTEIRO", "DECIMAL", "BOOLEANO", "TEXTO", "DATA"}
COMPARADORES = {"<", "<=", ">", ">=", "==", "<>"}
OPERADORES = {"+", "-", "*", "/"}


class ParserIFFARQL:
    def tokenizar(self, linha: str) -> List[Token]:
        tokens: List[Token] = []
        i = 0

        while i < len(linha):
            c = linha[i]
            if c.isspace():
                i += 1
                continue

            if c == '"':
                i += 1
                inicio = i
                partes = []
                while i < len(linha) and linha[i] != '"':
                    # suporte mínimo a \" dentro do texto
                    if linha[i] == "\\" and i + 1 < len(linha) and linha[i + 1] == '"':
                        partes.append(linha[inicio:i])
                        partes.append('"')
                        i += 2
                        inicio = i
                        continue
                    i += 1
                if i >= len(linha):
                    raise ErroSintaxe("Texto iniciado com aspas, mas sem aspas de fechamento.")
                partes.append(linha[inicio:i])
                tokens.append(Token("".join(partes), "TEXTO"))
                i += 1
                continue

            dois = linha[i:i + 2]
            if dois in {"<=", ">=", "==", "<>"}:
                tokens.append(Token(dois, "OPERADOR"))
                i += 2
                continue

            if c in "()+-*/=<>":
                tipo = "OPERADOR" if c in "+-*/=<>" else "SIMBOLO"
                tokens.append(Token(c, tipo))
                i += 1
                continue

            # número inteiro/decimal. O sinal é lido como operador para simplificar.
            m = re.match(r"\d+(?:\.\d+)?", linha[i:])
            if m:
                valor = m.group(0)
                tokens.append(Token(valor, "NUMERO"))
                i += len(valor)
                continue

            # palavra, nome de tabela/campo ou nome/caminho simples de arquivo.
            m = re.match(r"[^\s()=+*/<>-]+", linha[i:])
            if m:
                valor = m.group(0)
                tokens.append(Token(valor, "PALAVRA"))
                i += len(valor)
                continue

            raise ErroSintaxe(f"Caractere inesperado: {c}")

        return tokens

    def _token_valor(self, token: Token):
        return {
            "valor": token.valor,
            "citado": token.tipo == "TEXTO",
            "tipo_token": token.tipo,
        }

    def _condicao(self, tokens: List[Token]):
        if len(tokens) != 3:
            raise ErroSintaxe("A cláusula ONDE deve possuir apenas uma comparação.")
        if tokens[1].valor not in COMPARADORES:
            raise ErroSintaxe("Comparador inválido na cláusula ONDE.")
        return {
            "campo": tokens[0].valor,
            "operador": tokens[1].valor,
            "valor": self._token_valor(tokens[2]),
        }

    def _expressao(self, tokens: List[Token]):
        if len(tokens) == 1:
            return {"esquerda": self._token_valor(tokens[0]), "operador": None, "direita": None}
        if len(tokens) == 3 and tokens[1].valor in OPERADORES:
            return {
                "esquerda": self._token_valor(tokens[0]),
                "operador": tokens[1].valor,
                "direita": self._token_valor(tokens[2]),
            }
        raise ErroSintaxe("Expressão inválida em COM.")

    def parse(self, linha: str):
        linha = linha.strip()
        if not linha:
            return None

        # Para comandos de arquivo, todo o restante da linha é o nome do arquivo.
        primeiro = linha.split(maxsplit=1)[0]
        if primeiro in {"SALVARBD", "CARREGARBD", "CARREGARIFFARQL"}:
            partes = linha.split(maxsplit=1)
            if len(partes) != 2 or not partes[1].strip():
                raise ErroSintaxe(f"{primeiro} exige um nome de arquivo.")
            nome = partes[1].strip()
            if nome.startswith('"') and nome.endswith('"') and len(nome) >= 2:
                nome = nome[1:-1]
            return {"tipo": primeiro, "arquivo": nome}

        tokens = self.tokenizar(linha)
        if not tokens:
            return None

        comando = tokens[0].valor
        if comando not in COMANDOS:
            raise ErroSintaxe("Comando inválido. As palavras de comando devem estar em CAIXA ALTA.")

        if comando == "CRIATABELA":
            if len(tokens) < 5:
                raise ErroSintaxe("CRIATABELA incompleto.")
            nome = tokens[1].valor
            if tokens[2].valor != "(" or tokens[-1].valor != ")":
                raise ErroSintaxe("A definição da tabela deve ficar entre parênteses.")

            campos = []
            i = 3
            while i < len(tokens) - 1:
                if i + 1 >= len(tokens) - 1:
                    raise ErroSintaxe("Campo sem tipo em CRIATABELA.")
                nome_campo = tokens[i].valor
                tipo = tokens[i + 1].valor
                if tipo not in TIPOS:
                    raise ErroSintaxe(f"Tipo inválido: {tipo}")
                i += 2
                fk = None
                if i < len(tokens) - 1 and tokens[i].valor == "CHAVESTRANGEIRA":
                    if i + 1 >= len(tokens) - 1:
                        raise ErroSintaxe("CHAVESTRANGEIRA sem tabela referenciada.")
                    fk = tokens[i + 1].valor
                    i += 2
                campos.append({"nome": nome_campo, "tipo": tipo, "fk": fk})

            return {"tipo": comando, "tabela": nome, "campos": campos}

        if comando == "APAGATABELA":
            if len(tokens) != 2:
                raise ErroSintaxe("Uso: APAGATABELA nome_tabela")
            return {"tipo": comando, "tabela": tokens[1].valor}

        if comando == "INSERIREM":
            if len(tokens) < 6 or tokens[2].valor != "VALOR" or tokens[3].valor != "(" or tokens[-1].valor != ")":
                raise ErroSintaxe("Uso: INSERIREM tabela VALOR ( valores... )")
            valores = [self._token_valor(t) for t in tokens[4:-1]]
            return {"tipo": comando, "tabela": tokens[1].valor, "valores": valores}

        if comando in {"MOSTRADADOSDE", "APAGADADOSDE"}:
            if len(tokens) < 2:
                raise ErroSintaxe(f"{comando} exige o nome da tabela.")
            tabela = tokens[1].valor
            condicao = None
            if len(tokens) > 2:
                if tokens[2].valor != "ONDE":
                    raise ErroSintaxe("Esperado ONDE após o nome da tabela.")
                condicao = self._condicao(tokens[3:])
            return {"tipo": comando, "tabela": tabela, "condicao": condicao}

        if comando == "ATUALIZATABELA":
            if len(tokens) < 6:
                raise ErroSintaxe("ATUALIZATABELA incompleto.")
            tabela = tokens[1].valor
            i = 2
            alteracoes = []
            condicao = None

            while i < len(tokens):
                if tokens[i].valor == "ONDE":
                    condicao = self._condicao(tokens[i + 1:])
                    i = len(tokens)
                    break
                if tokens[i].valor != "COM":
                    raise ErroSintaxe("Esperado COM ou ONDE em ATUALIZATABELA.")
                if i + 2 >= len(tokens) or tokens[i + 2].valor != "=":
                    raise ErroSintaxe("Uso de COM inválido. Exemplo: COM preco = preco - 1000")
                campo = tokens[i + 1].valor
                i += 3
                inicio = i
                while i < len(tokens) and tokens[i].valor not in {"COM", "ONDE"}:
                    i += 1
                expressao = self._expressao(tokens[inicio:i])
                alteracoes.append({"campo": campo, "expressao": expressao})

            if not alteracoes:
                raise ErroSintaxe("Nenhuma alteração foi informada.")
            return {"tipo": comando, "tabela": tabela, "alteracoes": alteracoes, "condicao": condicao}

        raise ErroSintaxe("Comando reconhecido, mas ainda não interpretado.")
