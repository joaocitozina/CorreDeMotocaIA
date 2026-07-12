"""
Serviço (UseCase) de Gestão Financeira.

Orquestra a criação de lançamentos (ganhos e gastos) e a obtenção do
resumo financeiro do usuário, sempre passando pelas validações do
Domain antes de qualquer coisa chegar ao banco.
"""

from typing import List, Optional

from data.repositories.lancamento_repository import LancamentoRepository
from domain.entities.lancamento import Categoria, Lancamento, Natureza
from domain.validators.lancamento_validator import validar_lancamento


class FinancasService:
    """Caso de uso central da área financeira do app."""

    def __init__(self, lancamento_repository: LancamentoRepository = None):
        self._lancamento_repository = lancamento_repository or LancamentoRepository()

    def registrar_ganho(
        self, usuario_id: int, descricao: str, valor_texto: str, aplicativo: Optional[str] = None,
    ) -> Lancamento:
        """
        Registra uma corrida/ganho para o usuário.

        `aplicativo` é opcional (ex: "iFood", "Rappi") e identifica de
        qual app veio o ganho — usado depois por `obter_ganhos_por_app`
        para montar o gráfico da tela de Ganhos Detalhados. Quando não
        informado, o ganho aparece agrupado como "Outros" nesse relatório.
        """
        return self._registrar(
            usuario_id, Natureza.ENTRADA, Categoria.CORRIDA, descricao, valor_texto, aplicativo,
        )

    def registrar_gasto_pessoal(self, usuario_id: int, descricao: str, valor_texto: str) -> Lancamento:
        """Registra um gasto pessoal (alimentação, aluguel, etc.)."""
        return self._registrar(usuario_id, Natureza.SAIDA, Categoria.PESSOAL, descricao, valor_texto)

    def registrar_gasto_manutencao(self, usuario_id: int, descricao: str, valor_texto: str) -> Lancamento:
        """Registra um gasto de manutenção da moto (óleo, pneu, revisão, etc.)."""
        return self._registrar(usuario_id, Natureza.SAIDA, Categoria.MANUTENCAO, descricao, valor_texto)

    def _registrar(
        self, usuario_id: int, natureza: Natureza, categoria: Categoria,
        descricao: str, valor_texto: str, aplicativo: Optional[str] = None,
    ) -> Lancamento:
        descricao_limpa, valor_numerico = validar_lancamento(natureza, categoria, descricao, valor_texto)

        lancamento = Lancamento(
            usuario_id=usuario_id,
            natureza=natureza,
            categoria=categoria,
            descricao=descricao_limpa,
            valor=valor_numerico,
            aplicativo=aplicativo,
        )
        return self._lancamento_repository.salvar(lancamento)

    def excluir_lancamento(self, lancamento_id: int, usuario_id: int) -> None:
        self._lancamento_repository.excluir(lancamento_id, usuario_id)

    def listar_gastos_pessoais(self, usuario_id: int) -> List[Lancamento]:
        return self._lancamento_repository.listar_por_usuario(usuario_id, Categoria.PESSOAL)

    def listar_gastos_manutencao(self, usuario_id: int) -> List[Lancamento]:
        return self._lancamento_repository.listar_por_usuario(usuario_id, Categoria.MANUTENCAO)

    def listar_ganhos(self, usuario_id: int) -> List[Lancamento]:
        return self._lancamento_repository.listar_por_usuario(usuario_id, Categoria.CORRIDA)

    def obter_resumo_financeiro(self, usuario_id: int) -> dict:
        """
        Retorna o resumo usado pelo Dashboard: total ganho, total
        gasto (por categoria) e saldo final.
        """
        return self._lancamento_repository.calcular_totais(usuario_id)

    def obter_ganhos_por_app(self, usuario_id: int, periodo: Optional[str] = None) -> dict:
        """
        Ponte entre a Presentation (GanhosView) e o Repositório: retorna
        os ganhos já agrupados e somados por aplicativo, prontos para
        alimentar o gráfico e a listagem detalhada.

        Este serviço não faz nenhuma conta por conta própria — a
        agregação (SUM/GROUP BY) já vem pronta do
        `LancamentoRepository.obter_ganhos_por_app`. A camada de Domain
        só existe aqui como um ponto único de entrada para a
        Presentation, mantendo a regra de que Views nunca falam
        diretamente com Repositories.

        `periodo` aceita "diario", "semanal", "mensal" ou None (todo o
        histórico) — repassado direto para o repositório.
        """
        return self._lancamento_repository.obter_ganhos_por_app(usuario_id, periodo)
