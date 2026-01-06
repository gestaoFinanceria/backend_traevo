from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
from app.repositories.transacao_repository import TransacaoRepository
from app.repositories.orcamento_repository import OrcamentoRepository
from app.repositories.previsao_ia_repository import PrevisaoIARepository
from app.models.database_models import PrevisaoIA


class IAAnalysisService:
    """
    Serviço de Análise Inteligente (MVP - Simulação de IA).
    
    Para o MVP, implementa lógica matemática simples que simula
    uma IA de análise financeira:
    - Calcula tendências de gasto baseadas em histórico
    - Projeta gastos futuros usando média móvel
    - Determina índice de risco baseado em regras de negócio
    - Gera insights personalizados
    
    FUTURE: Substituir por modelos de ML reais (Regressão Linear,
    ARIMA, redes neurais, etc.)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.transacao_repo = TransacaoRepository(db)
        self.orcamento_repo = OrcamentoRepository(db)
        self.previsao_repo = PrevisaoIARepository(db)
    
    def gerar_previsao(self, usuario_id: str) -> PrevisaoIA:
        """
        Gera uma previsão completa para o usuário.
        
        Fluxo:
        1. Coleta histórico de transações (6 meses)
        2. Calcula média móvel de gastos
        3. Projeta gasto do mês atual
        4. Compara com orçamento disponível
        5. Calcula índice de risco
        6. Gera mensagem de insight personalizada
        
        Returns:
            PrevisaoIA gerada e salva no banco
        """
        now = datetime.now()
        
        # 1. Coletar dados históricos
        historico = self.transacao_repo.get_historico_para_ia(
            usuario_id=usuario_id,
            meses_anteriores=6
        )
        
        # 2. Calcular estatísticas
        estatisticas = self._calcular_estatisticas_historicas(historico)
        
        # 3. Projetar gasto do mês
        valor_projetado = self._projetar_gasto_mes(
            usuario_id=usuario_id,
            estatisticas=estatisticas
        )
        
        # 4. Calcular índice de risco
        indice_risco = self._calcular_indice_risco(
            usuario_id=usuario_id,
            valor_projetado=valor_projetado,
            estatisticas=estatisticas
        )
        
        # 5. Gerar mensagem de insight
        mensagem_insight = self._gerar_mensagem_insight(
            indice_risco=indice_risco,
            valor_projetado=valor_projetado,
            estatisticas=estatisticas
        )
        
        # 6. Salvar previsão no banco
        previsao = self.previsao_repo.create(
            usuario_id=usuario_id,
            valor_projetado=valor_projetado,
            indice_risco=indice_risco,
            mensagem_insight=mensagem_insight,
            mes_alvo=now.month,
            ano_alvo=now.year
        )
        
        return previsao
    
    def _calcular_estatisticas_historicas(
        self,
        historico: List
    ) -> Dict[str, Decimal]:
        """
        Calcula estatísticas do histórico de transações.
        
        Returns:
            dict com: media_gastos_mes, desvio_padrao, tendencia
        """
        if not historico:
            return {
                "media_gastos_mes": Decimal("0"),
                "desvio_padrao": Decimal("0"),
                "tendencia": "estavel",
                "total_historico": Decimal("0")
            }
        
        # Agrupar gastos por mês
        gastos_por_mes = {}
        for transacao in historico:
            if transacao.TIPO == "SAIDA":
                mes_key = f"{transacao.DATA_TRANSACAO.year}-{transacao.DATA_TRANSACAO.month}"
                gastos_por_mes[mes_key] = gastos_por_mes.get(mes_key, Decimal("0")) + transacao.VALOR
        
        # Calcular média
        valores = list(gastos_por_mes.values())
        media = sum(valores) / len(valores) if valores else Decimal("0")
        
        # Calcular desvio padrão simples
        if len(valores) > 1:
            variancia = sum((v - media) ** 2 for v in valores) / len(valores)
            desvio = Decimal(str(variancia ** 0.5))
        else:
            desvio = Decimal("0")
        
        # Detectar tendência (crescente, decrescente, estável)
        tendencia = "estavel"
        if len(valores) >= 3:
            ultimos_3 = valores[-3:]
            if ultimos_3[-1] > ultimos_3[0] * Decimal("1.1"):
                tendencia = "crescente"
            elif ultimos_3[-1] < ultimos_3[0] * Decimal("0.9"):
                tendencia = "decrescente"
        
        return {
            "media_gastos_mes": media,
            "desvio_padrao": desvio,
            "tendencia": tendencia,
            "total_historico": sum(valores)
        }
    
    def _projetar_gasto_mes(
        self,
        usuario_id: str,
        estatisticas: Dict
    ) -> Decimal:
        """
        Projeta o gasto total do mês atual usando média móvel ponderada.
        
        Lógica:
        - Se tendência crescente: projeta 10% acima da média
        - Se tendência decrescente: projeta 10% abaixo da média
        - Se estável: usa a média histórica
        """
        now = datetime.now()
        
        # Calcular gasto atual do mês (até hoje)
        totais_mes = self.transacao_repo.get_totais_por_tipo(
            usuario_id=usuario_id,
            mes=now.month,
            ano=now.year
        )
        
        gasto_atual_mes = totais_mes["total_saidas"]
        
        # Calcular dias decorridos e dias totais do mês
        dias_decorridos = now.day
        dias_no_mes = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).day if now.month < 12 else 31
        
        # Calcular média diária e projetar para o mês completo
        if dias_decorridos > 0:
            media_diaria = gasto_atual_mes / Decimal(str(dias_decorridos))
            projecao_base = media_diaria * Decimal(str(dias_no_mes))
        else:
            projecao_base = estatisticas["media_gastos_mes"]
        
        # Ajustar baseado na tendência
        tendencia = estatisticas["tendencia"]
        if tendencia == "crescente":
            projecao_final = projecao_base * Decimal("1.1")
        elif tendencia == "decrescente":
            projecao_final = projecao_base * Decimal("0.9")
        else:
            projecao_final = projecao_base
        
        return projecao_final.quantize(Decimal("0.01"))
    
    def _calcular_indice_risco(
        self,
        usuario_id: str,
        valor_projetado: Decimal,
        estatisticas: Dict
    ) -> str:
        """
        Calcula o índice de risco: VERDE, AMARELO ou VERMELHO.
        
        Regras de Negócio:
        - VERMELHO: Gasto projetado > 90% do orçamento total OU
                    Já gastou > 70% antes do dia 20
        - AMARELO: Gasto projetado entre 70-90% do orçamento OU
                   Tendência crescente preocupante
        - VERDE: Gasto projetado < 70% do orçamento E tendência estável
        """
        now = datetime.now()
        
        # Buscar orçamentos do mês atual
        orcamentos = self.orcamento_repo.find_all_ativos(usuario_id)
        
        if not orcamentos:
            # Sem orçamento definido: retorna AMARELO como cautela
            return "AMARELO"
        
        # Somar todos os limites de orçamento
        limite_total = sum(o.LIMITE_TOTAL for o in orcamentos)
        
        # Calcular percentual projetado
        percentual_projetado = (valor_projetado / limite_total * 100) if limite_total > 0 else 0
        
        # Calcular gasto atual
        totais = self.transacao_repo.get_totais_por_tipo(
            usuario_id=usuario_id,
            mes=now.month,
            ano=now.year
        )
        gasto_atual = totais["total_saidas"]
        percentual_atual = (gasto_atual / limite_total * 100) if limite_total > 0 else 0
        
        # REGRA 1: Risco crítico (VERMELHO)
        if percentual_projetado > 90:
            return "VERMELHO"
        
        if percentual_atual > 70 and now.day < 20:
            return "VERMELHO"
        
        # REGRA 2: Risco moderado (AMARELO)
        if percentual_projetado > 70:
            return "AMARELO"
        
        if estatisticas["tendencia"] == "crescente" and percentual_atual > 50:
            return "AMARELO"
        
        # REGRA 3: Risco baixo (VERDE)
        return "VERDE"
    
    def _gerar_mensagem_insight(
        self,
        indice_risco: str,
        valor_projetado: Decimal,
        estatisticas: Dict
    ) -> str:
        """
        Gera mensagem de insight personalizada baseada no índice de risco.
        
        Messages focam na UX "anti-ansiedade": são encorajadoras e práticas.
        """
        tendencia = estatisticas["tendencia"]
        
        mensagens = {
            "VERDE": [
                f"Ótimo trabalho! Seu gasto projetado é de R$ {valor_projetado:.2f}. Você está no controle!",
                f"Parabéns! Suas finanças estão saudáveis. Continue assim! 💚",
                f"Você está indo muito bem! Gasto projetado: R$ {valor_projetado:.2f}. Mantenha o ritmo!"
            ],
            "AMARELO": [
                f"Atenção: Gasto projetado de R$ {valor_projetado:.2f}. Considere revisar gastos não essenciais.",
                f"Seus gastos estão aumentando. Que tal revisar algumas categorias? 💛",
                f"Você está no limite! Gasto projetado: R$ {valor_projetado:.2f}. Planeje os próximos dias com cuidado."
            ],
            "VERMELHO": [
                f"Alerta! Gasto projetado de R$ {valor_projetado:.2f} pode exceder seu orçamento. Priorize o essencial! 🚨",
                f"Cuidado! Você está próximo do limite. Evite gastos não essenciais nos próximos dias.",
                f"Seus gastos estão acima do planejado. Vamos ajustar juntos? Revise suas prioridades. ❤️"
            ]
        }
        
        # Selecionar mensagem baseada no índice
        mensagens_disponiveis = mensagens[indice_risco]
        
        # Se tendência crescente, adicionar alerta extra
        if tendencia == "crescente" and indice_risco != "VERDE":
            return mensagens_disponiveis[0] + " Seus gastos têm aumentado nos últimos meses."
        
        return mensagens_disponiveis[0]
    
    def get_ultima_previsao(self, usuario_id: str) -> PrevisaoIA:
        """
        Busca a previsão mais recente do usuário.
        
        Se não existir, gera uma nova.
        """
        previsao = self.previsao_repo.find_mais_recente_por_usuario(usuario_id)
        
        if not previsao:
            previsao = self.gerar_previsao(usuario_id)
        
        return previsao