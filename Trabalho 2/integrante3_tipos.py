"""Integrante 3 - Tipos de dados, validações e operações.
Darley Rosa Socoloski
"""
from abc import ABC, abstractmethod
import re
import unicodedata
class ErroTipo(Exception):
    pass
def remover_acentos(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")
class TipoDado(ABC):
    nome = "BASE"
    @abstractmethod
    def converter(self, valor: str, citado: bool = False):
        pass
    def validar_python(self, valor) -> bool:
        return True
    def operar(self, operador: str, a, b):
        raise ErroTipo(f"Operação {operador} não permitida para {self.nome}.")
    def comparar(self, operador: str, a, b) -> bool:
        if operador == "==":
            return a == b
        if operador == "<>":
            return a != b
        raise ErroTipo(f"Comparação {operador} não permitida para {self.nome}.")
class TipoInteiro(TipoDado):
    nome = "INTEIRO"
    def converter(self, valor: str, citado: bool = False):
        if citado or not re.fullmatch(r"-?\d+", str(valor)):
            raise ErroTipo(f"'{valor}' não é um INTEIRO válido.")
        return int(valor)
    def validar_python(self, valor) -> bool:
        return isinstance(valor, int) and not isinstance(valor, bool)
    def operar(self, operador, a, b):
        if operador == "+": return a + b
        if operador == "-": return a - b
        if operador == "*": return a * b
        if operador == "/":
            if b == 0: raise ErroTipo("Divisão por zero.")
            resultado = a / b
            if not float(resultado).is_integer():
                raise ErroTipo("A divisão não resultou em INTEIRO.")
            return int(resultado)
        return super().operar(operador, a, b)
    def comparar(self, operador, a, b):
        if operador == "<": return a < b
        if operador == "<=": return a <= b
        if operador == ">": return a > b
        if operador == ">=": return a >= b
        return super().comparar(operador, a, b)
class TipoDecimal(TipoDado):
    nome = "DECIMAL"
    def converter(self, valor: str, citado: bool = False):
        if citado or not re.fullmatch(r"-?\d+(?:\.\d+)?", str(valor)):
            raise ErroTipo(f"'{valor}' não é um DECIMAL válido.")
        return float(valor)
    def validar_python(self, valor) -> bool:
        return isinstance(valor, (int, float)) and not isinstance(valor, bool)
    def operar(self, operador, a, b):
        if operador == "+": return float(a) + float(b)
        if operador == "-": return float(a) - float(b)
        if operador == "*": return float(a) * float(b)
        if operador == "/":
            if float(b) == 0: raise ErroTipo("Divisão por zero.")
            return float(a) / float(b)
        return super().operar(operador, a, b)
    def comparar(self, operador, a, b):
        if operador == "<": return a < b
        if operador == "<=": return a <= b
        if operador == ">": return a > b
        if operador == ">=": return a >= b
        return super().comparar(operador, a, b)
class TipoBooleano(TipoDado):
    nome = "BOOLEANO"
    def converter(self, valor: str, citado: bool = False):
        if citado:
            raise ErroTipo(f"'{valor}' não é BOOLEANO válido.")
        if str(valor) == "true": return True
        if str(valor) == "false": return False
        raise ErroTipo("BOOLEANO deve ser true ou false.")

    def validar_python(self, valor) -> bool:
        return isinstance(valor, bool)
class TipoTexto(TipoDado):
    nome = "TEXTO"
    def converter(self, valor: str, citado: bool = False):
        if not citado:
            raise ErroTipo("Valores TEXTO devem ser informados entre aspas duplas.")
        return remover_acentos(str(valor))
    def validar_python(self, valor) -> bool:
        return isinstance(valor, str)
    def operar(self, operador, a, b):
        if operador == "+":
            return remover_acentos(str(a) + str(b))
        return super().operar(operador, a, b)
    def comparar(self, operador, a, b):
        if operador == "<": return a < b
        if operador == "<=": return a <= b
        if operador == ">": return a > b
        if operador == ">=": return a >= b
        return super().comparar(operador, a, b)
class TipoData(TipoDado):
    nome = "DATA"
    DIAS_MESES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    def converter(self, valor: str, citado: bool = False):
        if not citado or not re.fullmatch(r"\d{2}/\d{2}/\d{4}", str(valor)):
            raise ErroTipo("DATA deve estar entre aspas no formato dd/mm/aaaa.")
        d, m, a = map(int, str(valor).split("/"))
        if not (1 <= a <= 9999 and 1 <= m <= 12):
            raise ErroTipo("DATA fora do intervalo permitido.")
        if not (1 <= d <= self.DIAS_MESES[m - 1]):
            raise ErroTipo("Dia inválido para o mês informado.")
        return f"{d:02d}/{m:02d}/{a:04d}"
    def validar_python(self, valor) -> bool:
        try:
            self.converter(str(valor), True)
            return True
        except ErroTipo:
            return False
    def _ordinal(self, data: str) -> int:
        d, m, a = map(int, data.split("/"))
        return (a - 1) * 365 + sum(self.DIAS_MESES[:m - 1]) + (d - 1)
    def _de_ordinal(self, total: int) -> str:
        maximo = 9999 * 365 - 1
        if total < 0 or total > maximo:
            raise ErroTipo("Resultado da DATA fora do intervalo 0001..9999.")
        a = total // 365 + 1
        resto = total % 365
        m = 1
        for dias in self.DIAS_MESES:
            if resto < dias:
                d = resto + 1
                return f"{d:02d}/{m:02d}/{a:04d}"
            resto -= dias
            m += 1
        raise ErroTipo("Falha ao calcular DATA.")
    def operar(self, operador, a, b):
        if not isinstance(b, int) or isinstance(b, bool):
            raise ErroTipo("DATA só pode somar ou subtrair um número INTEIRO de dias.")
        if operador == "+": return self._de_ordinal(self._ordinal(a) + b)
        if operador == "-": return self._de_ordinal(self._ordinal(a) - b)
        return super().operar(operador, a, b)
    def comparar(self, operador, a, b):
        x, y = self._ordinal(a), self._ordinal(b)
        if operador == "<": return x < y
        if operador == "<=": return x <= y
        if operador == ">": return x > y
        if operador == ">=": return x >= y
        if operador == "==": return x == y
        if operador == "<>": return x != y
        return super().comparar(operador, a, b)
TIPOS = {
    "INTEIRO": TipoInteiro,
    "DECIMAL": TipoDecimal,
    "BOOLEANO": TipoBooleano,
    "TEXTO": TipoTexto,
    "DATA": TipoData,
}
def criar_tipo(nome: str) -> TipoDado:
    if nome not in TIPOS:
        raise ErroTipo(f"Tipo desconhecido: {nome}")
    return TIPOS[nome]()
