"""
Tela de Login.

Responsável apenas por CAPTURAR os dados digitados, delegar a
autenticação ao AuthService (Domain) e traduzir o resultado — sucesso
ou exceção — em algo visual para o usuário. Nenhuma regra de negócio
mora aqui, só orquestração de interface.
"""

from typing import Callable

import customtkinter as ctk

from domain.entities.usuario import Usuario
from domain.exceptions.auth_exceptions import AuthException
from domain.services.auth_service import AuthService
from presentation.components.telefone_mask import aplicar_mascara_telefone
from presentation.components.widgets import (
    CampoTexto,
    criar_botao_link,
    criar_botao_primario,
    criar_mensagem_status,
    criar_subtitulo,
    criar_titulo,
)
from presentation.theme import colors, styles


class LoginView(ctk.CTkFrame):
    """
    Frame de Login, pensado para ser "trocado" dentro da janela
    principal do app (padrão comum em apps CustomTkinter de tela única
    com múltiplas telas/frames).
    """

    def __init__(
        self,
        master,
        ao_logar_com_sucesso: Callable[[Usuario], None],
        ao_ir_para_cadastro: Callable[[], None],
    ):
        super().__init__(master, fg_color=colors.FUNDO_PRINCIPAL)

        self._auth_service = AuthService()
        self._ao_logar_com_sucesso = ao_logar_com_sucesso
        self._ao_ir_para_cadastro = ao_ir_para_cadastro

        self._construir_interface()

    def _construir_interface(self) -> None:
        """
        Monta todos os widgets da tela, centralizados vertical e
        horizontalmente.

        CORREÇÃO DE LAYOUT (Etapa 4): a versão anterior fixava o card
        com `card.configure(height=430)` + `card.pack_propagate(False)`.
        Isso força TODO o conteúdo (título, subtítulo, 2 campos, erro,
        botão, link) a caber num espaço rígido de 430px — e quando o
        conteúdo real precisa de mais altura (por exemplo, quando a
        mensagem de erro aparece), o `pack()` comprime os ÚLTIMOS
        widgets adicionados para tentar caber, fazendo o botão "Entrar"
        virar uma linha esmagada e empurrando o link de cadastro para
        fora da área visível (clipping).

        A correção é simples: NUNCA travar a altura de um container que
        tem conteúdo dinâmico. Deixamos o card crescer livremente (sem
        `pack_propagate(False)` e sem `height` fixo) — só a LARGURA
        continua fixa, que é puramente estética e não depende de texto
        variável.
        """
        container_central = ctk.CTkFrame(self, fg_color="transparent")
        container_central.place(relx=0.5, rely=0.5, anchor="center")

        card = ctk.CTkFrame(
            container_central,
            fg_color=colors.FUNDO_SECUNDARIO,
            corner_radius=styles.RAIO_CARD,
            width=styles.LARGURA_CARD,
        )
        card.pack(fill="y")
        # Sem pack_propagate(False) e sem height fixo: o card agora
        # cresce em altura de acordo com o próprio conteúdo interno,
        # nunca mais espremendo os widgets do final da tela.

        conteudo = ctk.CTkFrame(card, fg_color="transparent", width=styles.LARGURA_CARD)
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_GRANDE, pady=styles.ESPACO_GRANDE)

        criar_titulo(conteudo, "Corre dos Motocas").pack(anchor="w", pady=(0, 4))
        criar_subtitulo(conteudo, "Entre para continuar sua corrida.").pack(
            anchor="w", pady=(0, 18)
        )

        self._campo_telefone = CampoTexto(
            conteudo, rotulo="Telefone", placeholder="16 99123-4567"
        )
        self._campo_telefone.pack(fill="x", pady=(5, 10))
        aplicar_mascara_telefone(self._campo_telefone.entry)

        self._campo_senha = CampoTexto(
            conteudo, rotulo="Senha", placeholder="Sua senha", mostrar_como_senha=True
        )
        self._campo_senha.pack(fill="x", pady=(5, 10))
        # Permite logar apertando Enter no campo de senha, sem precisar
        # clicar no botão — pequeno detalhe que melhora bastante a UX.
        self._campo_senha.entry.bind("<Return>", lambda _evento: self._tratar_login())

        self._mensagem_status = criar_mensagem_status(conteudo)
        self._mensagem_status.pack(fill="x", pady=(0, 6))

        # height=45 garante um tamanho mínimo visível para o botão
        # primário, independente de quanto espaço sobrar no card —
        # antes, era justamente esse botão que sofria o esmagamento.
        botao_entrar = criar_botao_primario(conteudo, "Entrar", self._tratar_login)
        botao_entrar.configure(height=45)
        botao_entrar.pack(fill="x", pady=(5, 10))

        botao_cadastro = criar_botao_link(
            conteudo, "Não tem conta? Cadastre-se", self._ao_ir_para_cadastro
        )
        botao_cadastro.pack(pady=(0, 2))

    def _tratar_login(self) -> None:
        """
        Lê os campos, chama o AuthService e trata cada tipo de erro de
        forma humanizada — sem nunca deixar uma exceção "estourar" e
        travar a interface.
        """
        self._limpar_mensagens()

        telefone = self._campo_telefone.get()
        senha = self._campo_senha.get()

        if not telefone or not senha:
            self._exibir_erro_geral("Preencha telefone e senha para continuar.")
            return

        try:
            usuario = self._auth_service.autenticar(telefone=telefone, senha=senha)
            self._ao_logar_com_sucesso(usuario)
        except AuthException as erro:
            self._exibir_erro_geral(str(erro))
        except Exception:
            # Rede de segurança final: qualquer erro inesperado (ex: banco
            # de dados indisponível) vira uma mensagem amigável em vez de
            # um traceback assustador para o usuário final.
            self._exibir_erro_geral(
                "Não foi possível entrar agora. Tente novamente em instantes."
            )

    def _exibir_erro_geral(self, mensagem: str) -> None:
        self._mensagem_status.configure(text=mensagem)

    def _limpar_mensagens(self) -> None:
        self._mensagem_status.configure(text="")
        self._campo_telefone.limpar_erro()
        self._campo_senha.limpar_erro()
