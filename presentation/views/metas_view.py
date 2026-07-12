"""
Tela de Metas.

Permite ao motoboy definir quanto pretende ganhar por dia e por mês, e
acompanhar visualmente o progresso em relação ao que já ganhou no
período (barra de progresso na cor laranja vibrante do tema).
"""

import customtkinter as ctk

from domain.entities.usuario import Usuario
from domain.exceptions.meta_exceptions import MetaInvalidaException
from domain.entities.meta import TipoMeta
from domain.services.metas_service import MetasService, ProgressoMeta
from presentation.components.financeiro_widgets import formatar_moeda
from presentation.components.widgets import criar_titulo
from presentation.theme import colors, styles

_ROTULO_POR_TIPO = {
    TipoMeta.DIARIA: "Meta diária",
    TipoMeta.MENSAL: "Meta mensal",
}
_DESCRICAO_POR_TIPO = {
    TipoMeta.DIARIA: "Quanto você quer ganhar hoje",
    TipoMeta.MENSAL: "Quanto você quer ganhar este mês",
}


class MetasView(ctk.CTkFrame):
    def __init__(self, master, usuario: Usuario):
        super().__init__(master, fg_color=colors.FUNDO_PRINCIPAL)

        self._usuario = usuario
        self._metas_service = MetasService()
        self._cards_por_tipo = {}

        self._construir_interface()
        self._atualizar_todos_os_cards()

    def _construir_interface(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=styles.ESPACO_GRANDE, pady=styles.ESPACO_GRANDE)

        criar_titulo(container, "Minhas metas").pack(anchor="w")
        ctk.CTkLabel(
            container, text="Defina objetivos e acompanhe o quanto já alcançou.",
            font=styles.FONTE_SUBTITULO, text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).pack(anchor="w", pady=(0, styles.ESPACO_GRANDE))

        linha_cards = ctk.CTkFrame(container, fg_color="transparent")
        linha_cards.pack(fill="x")
        linha_cards.grid_columnconfigure((0, 1), weight=1, uniform="metas")

        self._cards_por_tipo[TipoMeta.DIARIA] = self._construir_card_meta(linha_cards, TipoMeta.DIARIA)
        self._cards_por_tipo[TipoMeta.DIARIA]["frame"].grid(row=0, column=0, sticky="new", padx=(0, styles.ESPACO_PEQUENO))

        self._cards_por_tipo[TipoMeta.MENSAL] = self._construir_card_meta(linha_cards, TipoMeta.MENSAL)
        self._cards_por_tipo[TipoMeta.MENSAL]["frame"].grid(row=0, column=1, sticky="new", padx=(styles.ESPACO_PEQUENO, 0))

    def _construir_card_meta(self, master, tipo: TipoMeta) -> dict:
        """
        Monta um card de meta (diária ou mensal) e devolve as
        referências dos widgets que precisam ser atualizados depois
        (texto de valores, barra de progresso, percentual), num
        dicionário — evita criar uma subclasse só para isso.
        """
        card = ctk.CTkFrame(master, fg_color=colors.FUNDO_SECUNDARIO, corner_radius=styles.RAIO_CARD)

        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=styles.ESPACO_MEDIO)

        ctk.CTkLabel(
            conteudo, text=_ROTULO_POR_TIPO[tipo], font=(styles.FONTE_FAMILIA, 17, "bold"),
            text_color=colors.TEXTO_PRINCIPAL, anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            conteudo, text=_DESCRICAO_POR_TIPO[tipo], font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).pack(fill="x", pady=(0, styles.ESPACO_MEDIO))

        label_valores = ctk.CTkLabel(
            conteudo, text="", font=(styles.FONTE_FAMILIA, 22, "bold"),
            text_color=colors.TEXTO_PRINCIPAL, anchor="w",
        )
        label_valores.pack(fill="x")

        linha_barra = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha_barra.pack(fill="x", pady=(styles.ESPACO_PEQUENO, 4))

        # A barra de progresso usa a cor laranja vibrante do tema,
        # exatamente como pedido no briefing — é o "anel de progresso"
        # em formato de barra, já que o CustomTkinter não tem um
        # componente nativo de anel circular.
        barra_progresso = ctk.CTkProgressBar(
            linha_barra, height=14, corner_radius=8,
            fg_color=colors.BORDA, progress_color=colors.LARANJA_VIBRANTE,
        )
        barra_progresso.pack(fill="x")
        barra_progresso.set(0)

        label_percentual = ctk.CTkLabel(
            conteudo, text="", font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        )
        label_percentual.pack(fill="x", pady=(4, styles.ESPACO_MEDIO))

        botao_editar = ctk.CTkButton(
            conteudo, text="✏️  Editar meta", height=styles.ALTURA_BOTAO,
            corner_radius=styles.RAIO_BOTAO, fg_color=colors.LARANJA_VIBRANTE,
            hover_color=colors.LARANJA_HOVER, text_color=colors.TEXTO_PRINCIPAL,
            font=styles.FONTE_BOTAO, command=lambda: self._tratar_editar_meta(tipo),
        )
        botao_editar.pack(fill="x")

        return {
            "frame": card,
            "label_valores": label_valores,
            "barra_progresso": barra_progresso,
            "label_percentual": label_percentual,
        }

    # ------------------------------------------------------------------
    # Dados
    # ------------------------------------------------------------------

    def _atualizar_todos_os_cards(self) -> None:
        for tipo in (TipoMeta.DIARIA, TipoMeta.MENSAL):
            progresso = self._metas_service.obter_progresso(self._usuario.id, tipo)
            self._atualizar_card(tipo, progresso)

    def _atualizar_card(self, tipo: TipoMeta, progresso: ProgressoMeta) -> None:
        widgets = self._cards_por_tipo[tipo]

        if progresso.valor_meta is None:
            widgets["label_valores"].configure(
                text=f"{formatar_moeda(progresso.valor_atual)} ganhos até agora"
            )
            widgets["label_percentual"].configure(text="Nenhuma meta definida ainda — que tal criar uma?")
        else:
            widgets["label_valores"].configure(
                text=f"{formatar_moeda(progresso.valor_atual)} de {formatar_moeda(progresso.valor_meta)}"
            )
            widgets["label_percentual"].configure(text=f"{progresso.percentual_texto} da meta alcançados")

        widgets["barra_progresso"].set(progresso.proporcao)

        # Quando a meta é batida (100% ou mais), a barra vira verde para
        # comemorar visualmente — reforça o feedback positivo do saldo.
        cor_barra = colors.VERDE_SALDO_POSITIVO if progresso.proporcao >= 1.0 else colors.LARANJA_VIBRANTE
        widgets["barra_progresso"].configure(progress_color=cor_barra)

    # ------------------------------------------------------------------
    # Edição da meta
    # ------------------------------------------------------------------

    def _tratar_editar_meta(self, tipo: TipoMeta) -> None:
        """
        Abre um diálogo simples (CTkInputDialog) para o usuário digitar
        o novo valor da meta, valida e salva através do MetasService.

        O CTkInputDialog é modal: `get_input()` só retorna quando o
        usuário confirma ou cancela a janelinha. Se cancelar (ou fechar
        sem digitar nada), `get_input()` devolve None — nesse caso,
        simplesmente não fazemos nada, sem mostrar erro nenhum, já que
        cancelar não é um "erro" do usuário.
        """
        rotulo = _ROTULO_POR_TIPO[tipo]
        dialogo = ctk.CTkInputDialog(
            text=f"Novo valor para a {rotulo.lower()} (R$):", title=rotulo,
        )
        valor_digitado = dialogo.get_input()

        if valor_digitado is None:
            return

        try:
            self._metas_service.definir_meta(self._usuario.id, tipo, valor_digitado)
            progresso_atualizado = self._metas_service.obter_progresso(self._usuario.id, tipo)
            self._atualizar_card(tipo, progresso_atualizado)
        except MetaInvalidaException:
            # Mostra o erro no mesmo padrão humanizado das outras telas,
            # reabrindo o diálogo para o usuário tentar de novo.
            self._exibir_erro_e_tentar_novamente(tipo, rotulo)

    def _exibir_erro_e_tentar_novamente(self, tipo: TipoMeta, rotulo: str) -> None:
        dialogo_erro = ctk.CTkInputDialog(
            text=(
                f"Valor inválido. Digite um número maior que zero para a "
                f"{rotulo.lower()} (ex: 100,00):"
            ),
            title=f"{rotulo} — valor inválido",
        )
        valor_digitado = dialogo_erro.get_input()

        if valor_digitado is None:
            return

        try:
            self._metas_service.definir_meta(self._usuario.id, tipo, valor_digitado)
            progresso_atualizado = self._metas_service.obter_progresso(self._usuario.id, tipo)
            self._atualizar_card(tipo, progresso_atualizado)
        except MetaInvalidaException:
            # Se errar de novo, não insistimos infinitamente — o usuário
            # pode simplesmente clicar em "Editar meta" outra vez.
            pass
