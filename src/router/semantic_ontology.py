"""
Ontologia semântica para expansão de termos estatísticos.
Mapeia termos e sinônimos para intenções específicas e gera variações simples
de consulta para melhorar recall em buscas vetoriais.
"""
from typing import List, Dict, Set


class StatisticalOntology:
    """Ontologia para termos estatísticos e sinônimos."""

    VARIABILITY_TERMS = {
        # Português
        'variabilidade', 'variância', 'variancia', 'desvio padrão', 'desvio padrao',
        'dispersão', 'dispersao', 'espalhamento', 'volatilidade',
        'coeficiente de variação', 'coeficiente de variacao',
        # Inglês
        'variability', 'variance', 'standard deviation', 'std', 'var',
        'dispersion', 'spread', 'volatility', 'coefficient of variation', 'cv'
    }

    CENTRAL_TENDENCY_TERMS = {
        # Português
        'média', 'media', 'mediana', 'median', 'moda', 'mode',
        'tendência central', 'tendencia central', 'valor típico', 'valor tipico',
        # Inglês
        'mean', 'average', 'median', 'mode', 'central tendency', 'typical value'
    }

    INTERVAL_TERMS = {
        # Português
        'intervalo', 'mínimo', 'minimo', 'máximo', 'maximo', 'amplitude',
        'range', 'limites', 'valores extremos', 'extremos',
        # Inglês
        'interval', 'minimum', 'min', 'maximum', 'max', 'range', 'limits', 'extremes'
    }

    @classmethod
    def expand_query(cls, query: str) -> Dict[str, Set[str]]:
        """Expande query identificando termos presentes na ontologia.

        Returns:
            Dict com categorias detectadas e termos encontrados
        """
        query_lower = query.lower()
        detected = {
            'variability': set(),
            'central_tendency': set(),
            'interval': set()
        }

        for term in cls.VARIABILITY_TERMS:
            if term in query_lower:
                detected['variability'].add(term)

        for term in cls.CENTRAL_TENDENCY_TERMS:
            if term in query_lower:
                detected['central_tendency'].add(term)

        for term in cls.INTERVAL_TERMS:
            if term in query_lower:
                detected['interval'].add(term)

        return detected

    @classmethod
    def get_intent_priority(cls, query: str) -> str:
        """Determina intenção prioritária baseada na ontologia.

        Returns:
            'variability', 'central_tendency', 'interval', ou 'unknown'
        """
        detected = cls.expand_query(query)

        # Prioridade: variabilidade > tendência central > intervalo
        if detected['variability']:
            return 'variability'
        elif detected['central_tendency']:
            return 'central_tendency'
        elif detected['interval']:
            return 'interval'
        else:
            return 'unknown'

    @classmethod
    def generate_simple_expansions(cls, query: str) -> List[str]:
        """Gera variações simples da query substituindo termos por sinônimos

        A função tenta criar pequenas variações para melhorar recall do vector search:
        - Substitui palavras detectadas por sinônimos conhecidos
        - Adiciona formas em inglês/português quando aplicável

        Nota: Essa função é deliberadamente simples e determinística.
        """
        query_lower = query.lower()
        expansions = {query_lower}

        # Para cada grupo de termos, se detectado, adicione sinônimos/variantes
        if any(term in query_lower for term in cls.VARIABILITY_TERMS):
            expansions.add(query_lower.replace('variabilidade', 'variância'))
            expansions.add(query_lower + ' desvio padrão')
            expansions.add(query_lower + ' variance')

        if any(term in query_lower for term in cls.CENTRAL_TENDENCY_TERMS):
            expansions.add(query_lower.replace('média', 'mean'))
            expansions.add(query_lower + ' median')
            expansions.add(query_lower + ' average')

        if any(term in query_lower for term in cls.INTERVAL_TERMS):
            expansions.add(query_lower.replace('intervalo', 'range'))
            expansions.add(query_lower + ' min max')

        # Sempre adicionar forma sem stopwords (simples)
        # (remover artigos comuns para variações mínimas)
        stopwords = ['a', 'o', 'as', 'os', 'de', 'do', 'da', 'dos', 'das', 'e', 'com']
        tokens = [t for t in query_lower.split() if t not in stopwords]
        if len(tokens) > 1:
            expansions.add(' '.join(tokens))

        return list(expansions)
