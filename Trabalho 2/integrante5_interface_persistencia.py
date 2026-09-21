"""Integrante 5 - Persistência, CARREGARBD/CARREGARIFFARQL e terminal."""

import json
import os

from integrante1_parser import ParserIFFARQL, ErroSintaxe
from integrante4_banco import BancoDados, ExecutorBanco, ErroBanco


class SistemaIFFARQL:
    def __init__(self):
        self.banco = BancoDados()
        self.parser = ParserIFFARQL()
        self.executor = ExecutorBanco(self.banco)
        self.arquivo_atual = None
        self.arquivo_temporario = os.path.join(os.path.dirname(__file__), "_iffarql_autosave.json")

    def _salvar_em(self, caminho: str):
        with open(caminho, "w", encoding="utf-8") as arq:
            json.dump(self.banco.to_dict(), arq, ensure_ascii=False, indent=2)

    def _autosave(self):
        self._salvar_em(self.arquivo_atual or self.arquivo_temporario)

    def salvar_bd(self, caminho: str):
        self._salvar_em(caminho)
        self.arquivo_atual = caminho
        return f"Banco salvo em '{caminho}'."

    def carregar_bd(self, caminho: str):
        if not self.banco.vazio():
            raise ErroBanco("CARREGARBD só pode ser usado quando nenhuma tabela foi criada.")
        with open(caminho, "r", encoding="utf-8") as arq:
            dados = json.load(arq)
        self.banco.carregar_dict(dados)
        self.arquivo_atual = caminho
        return f"Banco carregado de '{caminho}'."

    def carregar_iffarql(self, caminho: str):
        if not self.banco.vazio():
            raise ErroBanco("CARREGARIFFARQL só pode ser usado quando nenhuma tabela foi criada.")

        mensagens = []
        with open(caminho, "r", encoding="utf-8") as arq:
            for numero, linha in enumerate(arq, start=1):
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    resultado = self.executar_linha(linha, permitir_carregar_script=False)
                    mensagens.append(f"Linha {numero}: OK - {self._resumo_resultado(resultado)}")
                except Exception as e:
                    # Cada comando é atômico. Um erro não deixa alteração parcial.
                    mensagens.append(f"Linha {numero}: ERRO - {e}")
        return mensagens

    def executar_linha(self, linha: str, permitir_carregar_script=True):
        comando = self.parser.parse(linha)
        if comando is None:
            return ""

        tipo = comando["tipo"]
        if tipo == "SALVARBD":
            return self.salvar_bd(comando["arquivo"])
        if tipo == "CARREGARBD":
            return self.carregar_bd(comando["arquivo"])
        if tipo == "CARREGARIFFARQL":
            if not permitir_carregar_script:
                raise ErroBanco("CARREGARIFFARQL não pode chamar outro CARREGARIFFARQL internamente.")
            return self.carregar_iffarql(comando["arquivo"])

        return self.executor.executar(comando, ao_alterar=self._autosave)

    def _resumo_resultado(self, resultado):
        if isinstance(resultado, list):
            return f"{len(resultado)} resultado(s)"
        return str(resultado)

    def imprimir_resultado(self, resultado):
        if isinstance(resultado, list):
            if not resultado:
                print("Nenhum registro encontrado.")
                return
            if resultado and isinstance(resultado[0], str):
                for linha in resultado:
                    print(linha)
                return
            colunas = list(resultado[0].keys())
            larguras = {c: max(len(c), max(len(str(r.get(c, ""))) for r in resultado)) for c in colunas}
            cabecalho = " | ".join(c.ljust(larguras[c]) for c in colunas)
            print(cabecalho)
            print("-+-".join("-" * larguras[c] for c in colunas))
            for registro in resultado:
                print(" | ".join(str(registro.get(c, "")).ljust(larguras[c]) for c in colunas))
        elif resultado:
            print(resultado)

    def executar_terminal(self):
        print("IFFARQL - SGBD simplificado")
        print("Digite SAIR para encerrar.\n")
        while True:
            try:
                linha = input("IFFARQL> ").strip()
                if linha == "SAIR":
                    break
                resultado = self.executar_linha(linha)
                self.imprimir_resultado(resultado)
            except (ErroSintaxe, ErroBanco, OSError, json.JSONDecodeError, ValueError) as e:
                print(f"ERRO: {e}")
            except KeyboardInterrupt:
                print("\nEncerrando.")
                break


if __name__ == "__main__":
    SistemaIFFARQL().executar_terminal()
