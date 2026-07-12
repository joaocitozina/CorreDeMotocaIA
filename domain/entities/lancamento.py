"""
Entidade de domínio: Lancamento.

Representa qualquer movimentação financeira do motoboy: tanto uma
ENTRADA (dinheiro de uma corrida) quanto uma SAÍDA (gasto pessoal ou
de manutenção da moto). Modelamos como uma única entidade — em vez de
"Ganho" e "Gasto" separados — porque as duas coisas compartilham os
mesmos atributos e só se diferenciam pela `natureza` e `categoria`,
o que evita duplicação de código nas camadas acima.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Natureza(str, Enum):
    """Se o lançamento é dinheiro entrando ou saindo do bolso do motoboy."""
    ENTRADA = "entrada"
    SAIDA = "saida"


class Categoria(str, Enum):
    """
    Classificação mais específica do lançamento.

    CORRIDA só é usada em lançamentos de ENTRADA; PESSOAL e MANUTENCAO
    só são usadas em lançamentos de SAIDA — essa regra é garantida pelo
    validador do Domain, não pela entidade em si.
    """
    CORRIDA = "corrida"
    PESSOAL = "pessoal"
    MANUTENCAO = "manutencao"


@dataclass
class Lancamento:
    """
    Representa um lançamento financeiro individual.

    Atributos:
        id: identificador único no banco (None enquanto não foi salvo).
        usuario_id: dono do lançamento — todo dado financeiro é sempre
            isolado por usuário, nunca compartilhado entre motoboys.
        natureza: entrada (ganho) ou saída (gasto).
        categoria: corrida, pessoal ou manutenção.
        descricao: texto livre descrevendo o lançamento (ex: "Troca de óleo").
        valor: valor em reais, sempre positivo — o sinal (+/-) é definido
            pela `natureza`, não pelo valor em si.
        aplicativo: nome do app de entrega que gerou o ganho (ex: "iFood",
            "Rappi"). Só faz sentido em lançamentos de ENTRADA/CORRIDA —
            fica None em gastos (pessoal/manutenção), já que "app de
            origem" não se aplica a uma despesa.
        data_registro: quando o lançamento foi criado.
    """

    usuario_id: int
    natureza: Natureza
    categoria: Categoria
    descricao: str
    valor: float
    id: Optional[int] = None
    aplicativo: Optional[str] = None
    data_registro: Optional[datetime] = None

    def eh_entrada(self) -> bool:
        """Atalho legível para checar se este lançamento é um ganho."""
        return self.natureza == Natureza.ENTRADA

    def valor_com_sinal(self) -> float:
        """
        Retorna o valor já com o sinal correto para somas diretas:
        positivo para entrada, negativo para saída. Muito usado no
        cálculo de saldo do Dashboard.
        """
        return self.valor if self.eh_entrada() else -self.valor
