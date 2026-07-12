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
        """Monta todos os widgets da tela, centralizados verticalmente."""
        container_central = ctk.CTkFrame(self, fg_color="transparent")
        container_central.place(relx=0.5, rely=0.5, anchor="center")

        card = ctk.CTkFrame(
            container_central,
            fg_color=colors.FUNDO_SECUNDARIO,
            corner_radius=styles.RAIO_CARD,
            width=styles.LARGURA_CARD,
        )
        card.pack()
        # Bloqueia o "encolhimento" automático do frame para manter a
        # largura consistente, independentemente do conteúdo interno.
        card.pack_propagate(False)
        card.configure(height=430)

        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_GRANDE, pady=styles.ESPACO_GRANDE)

        criar_titulo(conteudo, "Corre dos Motocas").pack(anchor="w")
        criar_subtitulo(conteudo, "Entre para continuar sua corrida.").pack(
            anchor="w", pady=(0, styles.ESPACO_GRANDE)
        )

        self._campo_telefone = CampoTexto(
            conteudo, rotulo="Telefone", placeholder="16 99123-4567"
        )
        self._campo_telefone.pack(fill="x", pady=(0, styles.ESPACO_MEDIO))
        aplicar_mascara_telefone(self._campo_telefone.entry)

        self._campo_senha = CampoTexto(
            conteudo, rotulo="Senha", placeholder="Sua senha", mostrar_como_senha=True
        )
        self._campo_senha.pack(fill="x")
        # Permite logar apertando Enter no campo de senha, sem precisar
        # clicar no botão — pequeno detalhe que melhora bastante a UX.
        self._campo_senha.entry.bind("<Return>", lambda _evento: self._tratar_login())

        self._mensagem_status = criar_mensagem_status(conteudo)
        self._mensagem_status.pack(fill="x", pady=(styles.ESPACO_MEDIO, 0))

        botao_entrar = criar_botao_primario(conteudo, "Entrar", self._tratar_login)
        botao_entrar.pack(fill="x", pady=(styles.ESPACO_MEDIO, styles.ESPACO_PEQUENO))

        botao_cadastro = criar_botao_link(
            conteudo, "Não tem conta? Cadastre-se", self._ao_ir_para_cadastro
        )
        botao_cadastro.pack()

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
