# ClearBank — Análise de Transações Financeiras

Projeto final do módulo de fundamentos práticos de Python aplicados à análise de dados.

O notebook lê o histórico mensal de transações exportado pela equipe de operações da
fintech fictícia **ClearBank**, valida e limpa os dados (o arquivo chega com campos
vazios, valores inválidos, datas mal formatadas e registros duplicados), calcula
métricas financeiras mensais, sinaliza transações potencialmente suspeitas, exibe um
relatório formatado no terminal e exporta o resultado em JSON.

Toda a solução principal usa **apenas módulos nativos** do Python (`csv`, `json`,
`datetime`, `os`) — sem bibliotecas externas.

---

## Estrutura do repositório

```
clearbank-analise/
├── desafio-final.ipynb   # notebook principal, com todas as saídas salvas
├── transacoes.csv        # arquivo de entrada (dados de teste)
├── analise_pandas.py     # RO1 — versão alternativa com pandas
├── relatorio.json        # saída gerada pelo notebook
├── grafico.png           # RO2 — gráfico gerado com matplotlib
└── README.md
```

---

## Como executar

### Google Colab

1. Acesse [colab.research.google.com](https://colab.research.google.com) e abra o `desafio-final.ipynb`.
2. No painel lateral **Arquivos**, faça upload de `transacoes.csv` e de `analise_pandas.py`.

<img width="1905" height="904" alt="image" src="https://github.com/user-attachments/assets/368a4245-d65b-4902-bc62-502ba44fe35a" />

3. Menu **Ambiente de execução → Executar tudo** (ou execute as células em ordem, de cima para baixo).

O Colab já vem com `pandas` e `matplotlib` instalados.

## Para os requisitos opcionais (a solução principal não precisa de nada além do Python):

### Jupyter Notebook local

Requer **Python 3.10 ou superior**.

Instale o Jupyter e as bibliotecas dos requisitos opcionais:

```bash
python -m pip install --user pandas matplotlib notebook
```

Abra o notebook:

```bash
python -m notebook desafio-final.ipynb
```

### Rodando a análise em pandas

```bash
python analise_pandas.py
```

---

## O que o notebook gera

### 1. No terminal (saída das células)

- **Resumo da limpeza** — total de linhas lidas, válidas, inválidas e duplicadas removidas;
- **Relatório mensal** — para cada mês (`AAAA-MM`): quantidade de transações, total de
  crédito, total de débito, saldo, valor médio, maior e menor valor, com os valores
  formatados no padrão brasileiro (`R$ 3.500,00`);
- **Período analisado** — data mais antiga, data mais recente e o número de dias entre elas;
- **Transações suspeitas** — toda transação acima de `LIMITE_SUSPEITO` (R$ 10.000,00),
  com id, cliente, data e valor.

### 2. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `relatorio.json` | Relatório consolidado: totais, período, resumo mensal e lista de suspeitas |
| `grafico.png` | Crédito/débito empilhados por mês + saldo mensal |

Estrutura do `relatorio.json`:

```json
{
  "gerado_em": "2026-08-28",
  "total_transacoes_validas": 29,
  "total_transacoes_invalidas": 8,
  "periodo": {
    "data_inicial": "2026-01-05",
    "data_final": "2026-07-02",
    "dias_analisados": 178
  },
  "limite_suspeito": 10000.0,
  "resumo_mensal": {
    "2026-01": {
      "quantidade": 4,
      "total_credito": 3500.0,
      "total_debito": 345.5,
      "saldo": 3154.5,
      "media": 961.38,
      "maior_valor": 3500.0,
      "menor_valor": 45.0
    }
  },
  "transacoes_suspeitas": [
    {
      "id": 6,
      "cliente_id": "CLI003",
      "data": "2026-02-14",
      "valor": 15000.0
    }
  ]
}
```

---

## Dados de entrada

O `transacoes.csv` tem 40 registros propositalmente com alguns valores "incorretos", para exercitar a validação:

| Categoria | Qtd. |
|---|---|
| Registros válidos | 29 (distribuídos em 7 meses: jan–jul/2026) |
| Registros inválidos | 8 |
| Registros duplicados | 3 |
| Transações acima de R$ 10.000,00 | 4 |

Os 8 registros inválidos cobrem cada regra de validação: `cliente_id` vazio, valor não
numérico (`abc`), valor vazio, valor negativo, valor zero, `tipo` fora de
`credito`/`debito`, data em formato errado (`13-05-2026`) e data inexistente
(`2026-06-31`).

---

## Regras de validação

Uma linha é descartada **silenciosamente** (sem interromper o programa) quando:

| Campo | Motivo do descarte |
|---|---|
| `id` | vazio ou não numérico |
| `cliente_id` | vazio |
| `data` | fora do formato `AAAA-MM-DD`, ou data inexistente no calendário |
| `tipo` | diferente de `credito` ou `debito` |
| `valor` | não numérico, ou menor/igual a zero |

**Duplicatas:** um registro é considerado repetido quando `data`, `cliente_id`, `tipo`,
`valor`, `descricao` e `categoria` coincidem com os de outro registro já processado. O
campo `id` é ignorado nessa comparação, porque o sistema de origem reemite a mesma
transação com um `id` novo.

---

## Organização do código

| Função | Responsabilidade |
|---|---|
| `ler_transacoes()` | Lê o CSV com `csv.DictReader` e retorna as linhas brutas |
| `validar_transacao()` | Valida uma única linha e devolve o registro limpo (ou `None`) |
| `limpar_transacoes()` | Aplica a validação em todas as linhas e remove duplicatas |
| `exibir_resumo_limpeza()` | Imprime o resumo da etapa de limpeza |
| `formatar_moeda()` | Formata um número no padrão brasileiro (`R$ 1.234,56`) |
| `gerar_relatorio()` | Agrupa por mês e calcula todas as métricas |
| `exibir_relatorio()` | Formata e imprime o relatório no terminal |
| `salvar_json()` | Salva o resultado em `relatorio.json` |
| `main()` | Orquestra o fluxo completo |

**Tratamento de erros** com `try/except` específico em cinco pontos: abertura do CSV
(`FileNotFoundError`), leitura em UTF-8 (`UnicodeDecodeError`), conversão de `valor`
para `float` (`ValueError`), conversão de `data` para `datetime` (`ValueError`) e
gravação do JSON (`OSError`).

---

## Requisitos opcionais

- **RO1 — pandas** (`analise_pandas.py`): refaz a leitura com `pd.read_csv()` e o
  agrupamento com `groupby()`, aplicando as mesmas regras de validação de forma
  vetorizada. Ao final, compara métrica a métrica com o `resumo_mensal` produzido pela
  solução nativa e confirma que os valores são idênticos.
- **RO2 — matplotlib** (`grafico.png`): gráfico de barras empilhadas com crédito e
  débito por mês (Opção C) somado a um painel de saldo mensal (Opção A), com título,
  rótulos nos eixos, grade e legenda.
