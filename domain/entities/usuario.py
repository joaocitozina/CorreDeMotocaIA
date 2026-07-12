"""
Entidade de domínio: Usuario.

Uma "entidade" representa um conceito central do negócio, independente
de como ele é salvo no banco ou exibido na tela. Ela não sabe nada sobre
SQLite nem sobre CustomTkinter — é só a representação do que é um usuário
dentro das regras do "Corre dos Motocas".
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Usuario:
    """
    Representa um motoboy cadastrado no sistema.

    Atributos:
        id: identificador único no banco (None enquanto ainda não foi salvo).
        nome_completo: nome do motoboy, usado nas telas e relatórios.
        telefone: telefone já validado e formatado no padrão PT-BR.
        cidade / estado_uf: localização, obtida via API do IBGE no cadastro.
        senha_hash: hash bcrypt da senha — NUNCA a senha em texto puro.
        aplicativos: lista de apps de entrega utilizados (iFood, Rappi...).
        ativo: permite "desativar" um usuário sem apagar seu histórico.
    """

    nome_completo: str
    telefone: str
    cidade: str
    estado_uf: str
    senha_hash: str
    id: Optional[int] = None
    aplicativos: List[str] = field(default_factory=list)
    ativo: bool = True

    def primeiro_nome(self) -> str:
        """
        Retorna apenas o primeiro nome do usuário.

        Útil para personalizar saudações na tela principal
        (ex: "Bom dia, João!") sem expor o nome completo o tempo todo.
        """
        return self.nome_completo.strip().split(" ")[0]
