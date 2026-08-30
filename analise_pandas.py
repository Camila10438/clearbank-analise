"""
ClearBank — Requisito Opcional 1 (RO1)
Versão alternativa da leitura e do agrupamento usando pandas.

Este arquivo é INDEPENDENTE da solução nativa do notebook (que usa apenas os
módulos csv/json/datetime). O objetivo é reproduzir exatamente as mesmas
métricas por outro caminho e provar que os dois resultados batem.

Uso:
    python analise_pandas.py

Ou, de dentro do notebook:
    from analise_pandas import analisar_com_pandas, comparar_resultados
"""

import json
import os

import pandas as pd

# As mesmas constantes usadas na solução nativa
ARQUIVO_ENTRADA = "transacoes.csv"
ARQUIVO_RELATORIO = "relatorio.json"
LIMITE_SUSPEITO = 10000.00
TIPOS_VALIDOS = ("credito", "debito")

# Colunas que definem uma transação duplicada (o 'id' é ignorado de propósito:
# registros repetidos pelo sistema de origem chegam com ids diferentes)
COLUNAS_CHAVE = ["data", "cliente_id", "tipo", "valor", "descricao", "categoria"]


def carregar_dataframe(caminho_arquivo=ARQUIVO_ENTRADA):
    """Lê o CSV com pd.read_csv(), sem conversão automática de tipos.

    dtype=str e keep_default_na=False garantem que a validação fique sob o
    nosso controle (e não sob o parser do pandas), reproduzindo exatamente as
    mesmas regras da solução nativa.
    """
    try:
        df = pd.read_csv(
            caminho_arquivo,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8",
        )
    except FileNotFoundError:
        print(f"[ERRO] Arquivo '{caminho_arquivo}' não encontrado.")
        return None

    return df


def limpar_dataframe(df):
    """Aplica as mesmas regras de validação da solução nativa, de forma vetorizada.

    Retorna: (df_limpo, qtd_invalidas, qtd_duplicadas)
    """
    total_lido = len(df)

    # Normaliza espaços em branco em todas as colunas de texto
    for coluna in df.columns:
        df[coluna] = df[coluna].str.strip()

    df["tipo"] = df["tipo"].str.lower()
    df["categoria"] = df["categoria"].str.lower()

    # --- Conversões: o que não converter vira NaN/NaT e é descartado ---
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["data"] = pd.to_datetime(df["data"], format="%Y-%m-%d", errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"].str.replace(",", ".", regex=False), errors="coerce")

    # --- Filtros de validade (equivalentes a validar_transacao()) ---
    valido = (
        df["id"].notna()                    # id preenchido e numérico
        & df["cliente_id"].ne("")           # cliente_id não vazio
        & df["data"].notna()                # data em AAAA-MM-DD e existente
        & df["tipo"].isin(TIPOS_VALIDOS)    # tipo credito ou debito
        & df["valor"].notna()               # valor numérico
        & df["valor"].gt(0)                 # valor maior que zero
    )

    df_valido = df[valido].copy()
    qtd_invalidas = total_lido - len(df_valido)

    # --- Remoção de duplicatas por conteúdo ---
    antes = len(df_valido)
    df_limpo = df_valido.drop_duplicates(subset=COLUNAS_CHAVE, keep="first").copy()
    qtd_duplicadas = antes - len(df_limpo)

    df_limpo["id"] = df_limpo["id"].astype(int)
    df_limpo["mes"] = df_limpo["data"].dt.strftime("%Y-%m")

    return df_limpo, qtd_invalidas, qtd_duplicadas


def agrupar_por_mes(df_limpo):
    """Agrupa por mês com groupby() e calcula as métricas mensais.

    Retorna um DataFrame indexado pelo mês (AAAA-MM).
    """
    # Métricas que não dependem do tipo da transação
    resumo = df_limpo.groupby("mes").agg(
        quantidade=("valor", "size"),
        media=("valor", "mean"),
        maior_valor=("valor", "max"),
        menor_valor=("valor", "min"),
    )

    # Somas separadas por tipo, realinhadas ao índice de meses
    soma_por_tipo = df_limpo.groupby(["mes", "tipo"])["valor"].sum().unstack(fill_value=0.0)

    resumo["total_credito"] = soma_por_tipo.get("credito", 0.0)
    resumo["total_debito"] = soma_por_tipo.get("debito", 0.0)
    resumo["saldo"] = resumo["total_credito"] - resumo["total_debito"]

    # Mesma ordem de colunas do relatório nativo, arredondada em 2 casas
    resumo = resumo[[
        "quantidade", "total_credito", "total_debito",
        "saldo", "media", "maior_valor", "menor_valor",
    ]].round(2)

    return resumo.sort_index()


def listar_suspeitas(df_limpo):
    """Filtra as transações acima do LIMITE_SUSPEITO."""
    suspeitas = df_limpo[df_limpo["valor"] > LIMITE_SUSPEITO]
    return suspeitas[["id", "cliente_id", "data", "valor"]].sort_values("data")


def analisar_com_pandas(caminho_arquivo=ARQUIVO_ENTRADA):
    """Executa o pipeline completo com pandas.

    Retorna um dicionário com o mesmo formato de 'resumo_mensal' da solução
    nativa, para permitir a comparação direta.
    """
    df = carregar_dataframe(caminho_arquivo)
    if df is None:
        return None

    df_limpo, qtd_invalidas, qtd_duplicadas = limpar_dataframe(df)
    resumo = agrupar_por_mes(df_limpo)

    print("=" * 45)
    print("ANÁLISE COM PANDAS (Requisito Opcional 1)")
    print("=" * 45)
    print(f"Total de linhas lidas: {len(df)}")
    print(f"Linhas válidas: {len(df_limpo)}")
    print(f"Linhas inválidas: {qtd_invalidas}")
    print(f"Linhas duplicadas removidas: {qtd_duplicadas}")
    print()
    print("--- Resumo mensal (groupby) ---")
    print(resumo.to_string())
    print()
    print("--- Transações suspeitas ---")
    suspeitas = listar_suspeitas(df_limpo)
    if suspeitas.empty:
        print("Nenhuma transação suspeita encontrada.")
    else:
        print(suspeitas.to_string(index=False))
    print()

    # Converte o DataFrame para o mesmo formato de dicionário do relatório nativo
    return resumo.to_dict(orient="index")


def comparar_resultados(resumo_pandas, resumo_nativo):
    """Compara métrica a métrica os dois resumos. Retorna True se forem idênticos."""
    print("=" * 45)
    print("COMPARAÇÃO: PANDAS x SOLUÇÃO NATIVA")
    print("=" * 45)

    if resumo_pandas is None or resumo_nativo is None:
        print("[ERRO] Um dos resumos não está disponível para comparação.")
        return False

    meses = sorted(set(resumo_pandas) | set(resumo_nativo))
    metricas = [
        "quantidade", "total_credito", "total_debito",
        "saldo", "media", "maior_valor", "menor_valor",
    ]

    divergencias = 0
    for mes in meses:
        if mes not in resumo_pandas or mes not in resumo_nativo:
            print(f"{mes}: DIVERGENTE (mês ausente em um dos resumos)")
            divergencias += 1
            continue

        diferentes = []
        for metrica in metricas:
            valor_pd = round(float(resumo_pandas[mes][metrica]), 2)
            valor_nt = round(float(resumo_nativo[mes][metrica]), 2)
            if abs(valor_pd - valor_nt) > 0.001:
                diferentes.append(f"{metrica} ({valor_pd} != {valor_nt})")

        if diferentes:
            print(f"{mes}: DIVERGENTE -> {', '.join(diferentes)}")
            divergencias += len(diferentes)
        else:
            print(f"{mes}: OK (7 métricas conferem)")

    print()
    if divergencias == 0:
        print(f"RESULTADO: os {len(meses)} meses conferem em todas as métricas.")
        print("As duas implementações produzem valores idênticos.")
        return True

    print(f"RESULTADO: {divergencias} divergência(s) encontrada(s).")
    return False


def carregar_relatorio_nativo(caminho_arquivo=ARQUIVO_RELATORIO):
    """Lê o relatorio.json gerado pela solução nativa do notebook."""
    try:
        with open(caminho_arquivo, mode="r", encoding="utf-8") as arquivo:
            return json.load(arquivo)["resumo_mensal"]
    except FileNotFoundError:
        print(f"[AVISO] '{caminho_arquivo}' não encontrado.")
        print("        Execute o notebook antes para gerar o relatório nativo.")
        return None
    except (json.JSONDecodeError, KeyError) as erro:
        print(f"[ERRO] '{caminho_arquivo}' está malformado: {erro}")
        return None


if __name__ == "__main__":
    # Garante que os caminhos relativos funcionem ao rodar de outra pasta
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")

    resumo_pd = analisar_com_pandas()
    resumo_nativo = carregar_relatorio_nativo()

    if resumo_pd is not None and resumo_nativo is not None:
        comparar_resultados(resumo_pd, resumo_nativo)
