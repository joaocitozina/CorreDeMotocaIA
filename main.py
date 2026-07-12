"""
Ponto de entrada da aplicação "Corre dos Motocas".

Esta classe App é a única responsável por saber "qual tela está
sendo exibida agora" — um padrão simples de troca de Frames dentro
de uma única janela CTk, muito comum em apps desktop com CustomTkinter.
Nem a LoginView nem a CadastroView conhecem uma à outra diretamente;
elas só recebem callbacks (`ao_ir_para_cadastro`, `ao_logar_com_sucesso`
etc.) e quem decide o que fazer com isso é sempre o App.
"""

import customtkinter as ctk

from config.settings import APP_NAME
from data.database.connection import db_connection
from domain.entities.usuario import Usuario
from presentation.theme import colors
from presentation.views.cadastro_view import CadastroView
from presentation.views.login_view import LoginView
from presentation.views.painel_principal_view import PainelPrincipalView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Garante que o banco e as tabelas existam antes de qualquer
        # tela tentar consultar ou salvar dados.
        db_connection.criar_tabelas()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # base neutra; as cores reais vêm de presentation/theme

        self.title(APP_NAME)
        self.geometry("980x720")
        self.minsize(480, 640)
        self.configure(fg_color=colors.FUNDO_PRINCIPAL)

        self._frame_atual: ctk.CTkFrame | None = None
        self.mostrar_login()

    # ------------------------------------------------------------------
    # Roteamento entre telas
    # ------------------------------------------------------------------

    def mostrar_login(self) -> None:
        self._trocar_frame(
            LoginView(
                self,
                ao_logar_com_sucesso=self._ao_login_bem_sucedido,
                ao_ir_para_cadastro=self.mostrar_cadastro,
            )
        )

    def mostrar_cadastro(self) -> None:
        self._trocar_frame(
            CadastroView(
                self,
                ao_cadastrar_com_sucesso=self._ao_cadastro_bem_sucedido,
                ao_ir_para_login=self.mostrar_login,
            )
        )

    def mostrar_painel_principal(self, usuario: Usuario) -> None:
        self._trocar_frame(
            PainelPrincipalView(self, usuario=usuario, ao_sair=self.mostrar_login)
        )

    def _trocar_frame(self, novo_frame: ctk.CTkFrame) -> None:
        """
        Remove a tela atual da janela (se houver) e exibe a nova.

        Destruir o frame anterior (em vez de só escondê-lo) evita
        acúmulo de widgets "fantasmas" na memória conforme o usuário
        navega entre as telas repetidamente.
        """
        if self._frame_atual is not None:
            self._frame_atual.destroy()

        self._frame_atual = novo_frame
        self._frame_atual.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Reações a eventos de autenticação
    # ------------------------------------------------------------------

    def _ao_login_bem_sucedido(self, usuario: Usuario) -> None:
        self.mostrar_painel_principal(usuario)

    def _ao_cadastro_bem_sucedido(self, usuario: Usuario) -> None:
        # Após cadastrar, mandamos o usuário para o Login para que ele
        # já entre com as credenciais recém-criadas.
        self.mostrar_login()


if __name__ == "__main__":
    app = App()
    app.mainloop()
