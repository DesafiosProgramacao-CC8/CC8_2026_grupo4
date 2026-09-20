from dataclasses import dataclass
from typing import Any, Generator, Optional, Tuple


@dataclass
class NoAVL:
    chave: str
    valor: Any
    esquerda: Optional["NoAVL"] = None
    direita: Optional["NoAVL"] = None
    altura: int = 1


class ArvoreAVL:
    """Árvore AVL implementada manualmente para indexação e busca."""

    def __init__(self):
        self.raiz: Optional[NoAVL] = None
        self.tamanho = 0

    def _altura(self, no: Optional[NoAVL]) -> int:
        return no.altura if no else 0

    def _atualizar_altura(self, no: NoAVL) -> None:
        no.altura = 1 + max(self._altura(no.esquerda), self._altura(no.direita))

    def _fator_balanceamento(self, no: NoAVL) -> int:
        return self._altura(no.esquerda) - self._altura(no.direita)

    def _rotacao_direita(self, y: NoAVL) -> NoAVL:
        x = y.esquerda
        t2 = x.direita

        x.direita = y
        y.esquerda = t2

        self._atualizar_altura(y)
        self._atualizar_altura(x)
        return x

    def _rotacao_esquerda(self, x: NoAVL) -> NoAVL:
        y = x.direita
        t2 = y.esquerda

        y.esquerda = x
        x.direita = t2

        self._atualizar_altura(x)
        self._atualizar_altura(y)
        return y

    def _rebalancear(self, no: NoAVL) -> NoAVL:
        self._atualizar_altura(no)
        fator = self._fator_balanceamento(no)

        if fator > 1:
            if self._fator_balanceamento(no.esquerda) < 0:
                no.esquerda = self._rotacao_esquerda(no.esquerda)
            return self._rotacao_direita(no)

        if fator < -1:
            if self._fator_balanceamento(no.direita) > 0:
                no.direita = self._rotacao_direita(no.direita)
            return self._rotacao_esquerda(no)

        return no

    def inserir(self, chave: str, valor: Any) -> None:
        inseriu_novo = False

        def _inserir(no: Optional[NoAVL], chave_: str, valor_: Any) -> NoAVL:
            nonlocal inseriu_novo

            if no is None:
                inseriu_novo = True
                return NoAVL(chave_, valor_)

            if chave_ < no.chave:
                no.esquerda = _inserir(no.esquerda, chave_, valor_)
            elif chave_ > no.chave:
                no.direita = _inserir(no.direita, chave_, valor_)
            else:
                no.valor = valor_
                return no

            return self._rebalancear(no)

        self.raiz = _inserir(self.raiz, chave, valor)
        if inseriu_novo:
            self.tamanho += 1

    def buscar(self, chave: str) -> Any:
        no = self.raiz

        while no:
            if chave == no.chave:
                return no.valor
            if chave < no.chave:
                no = no.esquerda
            else:
                no = no.direita

        return None

    def itens(self) -> Generator[Tuple[str, Any], None, None]:
        def _percorrer(no: Optional[NoAVL]):
            if no:
                yield from _percorrer(no.esquerda)
                yield no.chave, no.valor
                yield from _percorrer(no.direita)

        yield from _percorrer(self.raiz)

    def valores(self):
        for _, valor in self.itens():
            yield valor

    def limpar(self) -> None:
        self.raiz = None
        self.tamanho = 0
