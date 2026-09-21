"""Integrante 2 - Árvore AVL.

Este arquivo reaproveita a implementação de ArvoreAVL do Trabalho Integrador I
(integrante2_arvore_avl.py) e acrescenta a remoção, necessária ao IFFARQL.
"""

from dataclasses import dataclass
from typing import Any, Generator, Optional, Tuple


@dataclass
class NoAVL:
    chave: int
    valor: Any
    esquerda: Optional["NoAVL"] = None
    direita: Optional["NoAVL"] = None
    altura: int = 1


class ArvoreAVL:
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

    def inserir(self, chave: int, valor: Any) -> None:
        inseriu_novo = False

        def _inserir(no: Optional[NoAVL], chave_: int, valor_: Any) -> NoAVL:
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

    def buscar(self, chave: int) -> Any:
        no = self.raiz
        while no:
            if chave == no.chave:
                return no.valor
            no = no.esquerda if chave < no.chave else no.direita
        return None

    def remover(self, chave: int) -> bool:
        removeu = False

        def _menor(no: NoAVL) -> NoAVL:
            atual = no
            while atual.esquerda:
                atual = atual.esquerda
            return atual

        def _remover(no: Optional[NoAVL], chave_: int) -> Optional[NoAVL]:
            nonlocal removeu
            if no is None:
                return None

            if chave_ < no.chave:
                no.esquerda = _remover(no.esquerda, chave_)
            elif chave_ > no.chave:
                no.direita = _remover(no.direita, chave_)
            else:
                removeu = True
                if no.esquerda is None:
                    return no.direita
                if no.direita is None:
                    return no.esquerda

                sucessor = _menor(no.direita)
                no.chave = sucessor.chave
                no.valor = sucessor.valor
                # remove o sucessor sem alterar o controle externo novamente
                def _remover_sucessor(n: Optional[NoAVL], chave_s: int) -> Optional[NoAVL]:
                    if n is None:
                        return None
                    if chave_s < n.chave:
                        n.esquerda = _remover_sucessor(n.esquerda, chave_s)
                    elif chave_s > n.chave:
                        n.direita = _remover_sucessor(n.direita, chave_s)
                    else:
                        if n.esquerda is None:
                            return n.direita
                        if n.direita is None:
                            return n.esquerda
                    return self._rebalancear(n)
                no.direita = _remover_sucessor(no.direita, sucessor.chave)

            return self._rebalancear(no) if no else None

        self.raiz = _remover(self.raiz, chave)
        if removeu:
            self.tamanho -= 1
        return removeu

    def itens(self) -> Generator[Tuple[int, Any], None, None]:
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
