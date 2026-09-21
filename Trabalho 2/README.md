Trabalho Integrador II — IFFARQL
1. Introdução

O IFFARQL é um Sistema Gerenciador de Banco de Dados (SGBD) simplificado, desenvolvido para execução em ambiente de terminal.

O projeto tem como objetivo aplicar conceitos de Programação Orientada a Objetos, estruturas de dados, manipulação de arquivos e gerenciamento de dados, utilizando uma linguagem de comandos própria, inspirada no SQL, porém escrita em português e com um conjunto reduzido de operações.

O sistema permite criar, alterar, consultar e excluir tabelas e registros, além de salvar e carregar bancos de dados.

Os registros são armazenados utilizando uma árvore de busca, tendo o campo id como chave de cada nó, evitando o uso de vetores para armazenamento dos registros.

2. Funcionalidades

## O sistema disponibiliza as seguintes operações:

CRIATABELA — cria uma nova tabela.

APAGATABELA — remove uma tabela vazia.

INSERIREM — insere novos registros.

ATUALIZATABELA — atualiza registros existentes.

APAGADADOSDE — remove registros.

MOSTRADADOSDE — consulta e exibe registros.

SALVARBD — salva o banco de dados em arquivo.

CARREGARBD — carrega um banco de dados previamente salvo.

CARREGARIFFARQL — executa comandos armazenados em um arquivo .txt.

O sistema também possui suporte a chaves estrangeiras, permitindo relacionamentos do tipo 1:N entre tabelas.

3. Tipos de dados

## São suportados cinco tipos de dados:

Tipo	Descrição
INTEIRO	Valores inteiros
DECIMAL	Valores decimais
BOOLEANO	Valores verdadeiro ou falso
TEXTO	Palavras ou frases
DATA	Datas no formato dd/mm/aaaa

O campo id é criado automaticamente em todas as tabelas e possui incremento automático. O usuário não pode criar ou alterar manualmente esse campo.

## Textos com acentuação são normalizados. Por exemplo:

"Adão"

## é armazenado como:

"Adao"

4. Exemplos de comandos
Criar tabela
CRIATABELA pessoa (
nome TEXTO
idade INTEIRO
altura DECIMAL
nascimento DATA
)

Criar tabela com chave estrangeira
CRIATABELA endereco (
rua TEXTO
numero INTEIRO
idPessoa INTEIRO CHAVESTRANGEIRA pessoa
)

Inserir registro
INSERIREM pessoa VALOR ("Joao da Silva" 20 1.75 "10/05/2006")

Consultar registros
MOSTRADADOSDE pessoa

## Ou utilizando uma condição:

MOSTRADADOSDE pessoa ONDE idade >= 18

Atualizar registros
ATUALIZATABELA pessoa COM idade = 21 ONDE nome == "Joao da Silva"

Também são permitidas operações matemáticas em atualizações, por exemplo:

ATUALIZATABELA pessoa COM idade = idade + 1 ONDE idade >= 18

Remover registros
APAGADADOSDE pessoa ONDE idade < 18

Salvar banco de dados
SALVARBD banco

Carregar banco de dados
CARREGARBD banco

Executar arquivo IFFARQL
CARREGARIFFARQL comandos.txt

5. Tecnologias utilizadas

Linguagem: Python

Paradigma: Programação Orientada a Objetos

Estrutura de dados: Árvore de busca

Persistência: Arquivos

Interface: Terminal/linha de comando

6. Exemplo de arquivo para CARREGARIFFARQL:

CRIATABELA pessoa ( nome TEXTO idade INTEIRO altura DECIMAL nascimento DATA )
INSERIREM pessoa VALOR ("Maria Silva" 20 1.65 "15/03/2006")
INSERIREM pessoa VALOR ("Joao Souza" 25 1.80 "20/07/2001")
MOSTRADADOSDE pessoa
ATUALIZATABELA pessoa COM idade = idade + 1 ONDE idade >= 20
MOSTRADADOSDE pessoa

Cada linha do arquivo representa um comando que será interpretado pelo sistema.

7. Integridade e transações

O sistema busca manter a consistência dos dados por meio de validações antes da conclusão das operações.

## Entre as principais validações estão:

Não permitir tabelas com nomes repetidos.

Não permitir registros com valores nulos.

Validar os tipos dos valores inseridos.

Validar datas conforme o formato definido.

Garantir a existência de tabelas referenciadas por chaves estrangeiras.

Impedir a exclusão de registros que estejam sendo referenciados por outras tabelas.

Impedir a exclusão de tabelas que possuam registros.

Reverter alterações quando ocorrer um erro durante uma operação.

Manter o próximo valor de id mesmo após a exclusão de registros.

Após operações que alteram o banco, os dados devem ser persistidos conforme as regras definidas no trabalho.

8. Limitações

Por se tratar de um SGBD desenvolvido para fins didáticos, o sistema possui algumas limitações:

Apenas os cinco tipos de dados especificados são suportados.

São permitidos somente relacionamentos do tipo 1:N.

As consultas permitem apenas uma condição por ONDE.

Não são suportadas operações equivalentes a JOIN, GROUP BY, ORDER BY ou outras funcionalidades avançadas do SQL.

O sistema funciona exclusivamente através do terminal.

O controle de concorrência entre diferentes usuários ou processos não é implementado.

As regras de datas seguem as especificações simplificadas do trabalho, desconsiderando anos bissextos.

A estrutura de armazenamento utiliza a árvore de busca baseada no campo id.

9. Objetivo acadêmico

O projeto tem como principal objetivo consolidar os conhecimentos adquiridos durante o curso, especialmente em:

Programação Orientada a Objetos;

Polimorfismo;

Estruturas de dados;

Árvores de busca;

Manipulação de arquivos;

Validação e tratamento de erros;

Persistência de dados;

Integridade de informações;

Implementação de uma linguagem de comandos simplificada.