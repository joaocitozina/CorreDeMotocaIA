"""
Exceções customizadas da área de Autenticação.

Criar exceções específicas (em vez de usar Exception genérica ou
ValueError para tudo) permite que a camada de Presentation capture
cada erro separadamente e mostre uma mensagem humanizada e precisa
para o usuário, sem precisar "adivinhar" o que deu errado a partir
de uma string solta.
"""


class AuthException(Exception):
    """
    Classe-base de todas as exceções de autenticação.

    Serve para que a interface gráfica possa, se quiser, capturar
    "qualquer erro de autenticação" com um único except AuthException,
    sem precisar listar cada subclasse manualmente.
    """
    pass


class CampoObrigatorioException(AuthException):
    """Lançada quando um campo obrigatório do formulário está vazio."""

    def __init__(self, nome_campo: str):
        self.nome_campo = nome_campo
        super().__init__(f"O campo '{nome_campo}' é obrigatório e não foi preenchido.")


class SenhaInvalidaException(AuthException):
    """
    Lançada quando a senha não atende aos critérios mínimos de segurança.

    Guardamos os "motivos" em lista para que a tela possa exibir,
    se quiser, um checklist detalhado (ex: "faltou 1 caractere especial")
    em vez de uma mensagem genérica só.
    """

    def __init__(self, motivos: list[str]):
        self.motivos = motivos
        mensagem = "A senha não atende aos requisitos mínimos: " + "; ".join(motivos)
        super().__init__(mensagem)


class SenhasNaoConferemException(AuthException):
    """Lançada quando 'senha' e 'confirmação de senha' são diferentes."""

    def __init__(self):
        super().__init__("A senha e a confirmação de senha não são iguais.")


class TelefoneInvalidoException(AuthException):
    """Lançada quando o telefone não segue o padrão brasileiro (XX 9XXXX-XXXX)."""

    def __init__(self):
        super().__init__(
            "Telefone inválido. Use o formato brasileiro com DDD e o 9º dígito, "
            "por exemplo: 16 99123-4567."
        )


class UsuarioJaExisteException(AuthException):
    """Lançada ao tentar cadastrar um telefone que já está em uso."""

    def __init__(self, telefone: str):
        self.telefone = telefone
        super().__init__(f"Já existe um cadastro com o telefone {telefone}.")


class CredenciaisInvalidasException(AuthException):
    """
    Lançada no login quando telefone ou senha estão incorretos.

    Importante: por segurança, NUNCA informamos qual dos dois campos
    está errado (evita que alguém mal-intencionado descubra se um
    telefone existe ou não no sistema por tentativa e erro).
    """

    def __init__(self):
        super().__init__("Telefone ou senha incorretos. Verifique seus dados e tente novamente.")


class LocalizacaoInvalidaException(AuthException):
    """Lançada quando cidade/estado não foram selecionados ou são inválidos."""

    def __init__(self):
        super().__init__("Selecione um estado e uma cidade válidos para continuar.")


class AplicativosNaoSelecionadosException(AuthException):
    """Lançada quando o usuário não marcou nenhum app de entrega utilizado."""

    def __init__(self):
        super().__init__("Selecione ao menos um aplicativo de entrega que você utiliza.")
