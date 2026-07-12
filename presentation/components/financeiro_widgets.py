"""
Componentes visuais da área financeira: cards de destaque numérico e
barras de progresso categorizadas — usados principalmente no Dashboard.
"""

import customtkinter as ctk

from presentation.theme import colors, styles


def formatar_moeda(valor: float) -> str:
    """
    Formata um número float no padrão monetário brasileiro:
    "R$ 1.234,56". Centralizado aqui porque várias telas (Dashboard,
    Gastos, Simulação) precisam exibir valores em Real.
    """
    texto = f"{abs(valor):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    sinal = "-" if valor < 0 else ""
    return f"{sinal}R$ {texto}"


class CardValor(ctk.CTkFrame):
    """
    Card compacto com um rótulo e um valor monetário em destaque.

    A cor do valor muda dinamicamente: verde para saldo positivo,
    vermelho para negativo — conforme pedido no briefing visual do app.
    """

    def __init__(self, master, rotulo: str, **kwargs):
        super().__init__(
            master, fg_color=colors.FUNDO_SECUNDARIO,
            corner_radius=styles.RAIO_CARD, **kwargs,
        )

        conteudo = ctk.CTkFrame(self, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=styles.ESPACO_MEDIO)

        ctk.CTkLabel(
            conteudo, text=rotulo, font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).pack(fill="x")

        self._label_valor = ctk.CTkLabel(
            conteudo, text="R$ 0,00", font=(styles.FONTE_FAMILIA, 24, "bold"),
            text_color=colors.TEXTO_PRINCIPAL, anchor="w",
        )
        self._label_valor.pack(fill="x", pady=(4, 0))

    def definir_valor(self, valor: float, colorir_por_sinal: bool = False) -> None:
        """
        Atualiza o valor exibido. Se `colorir_por_sinal` for True, a cor
        do texto muda automaticamente: verde se >= 0, vermelho se < 0
        (usado no card de Saldo). Para os demais cards (ganhos, gastos),
        deixamos a cor padrão em branco, já que "gasto" não é uma coisa
        ruim em si — é só informação.
        """
        self._label_valor.configure(text=formatar_moeda(valor))

        if colorir_por_sinal:
            cor = colors.VERDE_SALDO_POSITIVO if valor >= 0 else colors.VERMELHO_SALDO_NEGATIVO
            self._label_valor.configure(text_color=cor)


class BarraProgressoCategoria(ctk.CTkFrame):
    """
    Uma linha de "gráfico" simples: rótulo + valor + CTkProgressBar,
    representando a proporção de uma categoria de gasto em relação ao
    total ganho. Usamos a barra de progresso nativa do CustomTkinter
    (em vez de uma lib de gráficos pesada) para manter a UI leve e
    consistente com o tema.
    """

    def __init__(self, master, rotulo: str, cor_barra: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._cor_barra = cor_barra

        linha_topo = ctk.CTkFrame(self, fg_color="transparent")
        linha_topo.pack(fill="x")

        ctk.CTkLabel(
            linha_topo, text=rotulo, font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).pack(side="left")

        self._label_valor = ctk.CTkLabel(
            linha_topo, text="R$ 0,00", font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_PRINCIPAL, anchor="e",
        )
        self._label_valor.pack(side="right")

        self._barra = ctk.CTkProgressBar(
            self, height=10, corner_radius=6,
            fg_color=colors.BORDA, progress_color=cor_barra,
        )
        self._barra.pack(fill="x", pady=(4, 0))
        self._barra.set(0)

    def atualizar(self, valor: float, valor_total_referencia: float) -> None:
        """
        Atualiza o texto e o preenchimento da barra.

        `valor_total_referencia` é o "100%" da barra (normalmente o
        total ganho no período) — se for zero, mantemos a barra vazia
        em vez de causar uma divisão por zero.
        """
        self._label_valor.configure(text=formatar_moeda(valor))

        proporcao = (valor / valor_total_referencia) if valor_total_referencia > 0 else 0
        self._barra.set(min(max(proporcao, 0), 1))
