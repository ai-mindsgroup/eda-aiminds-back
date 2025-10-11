# README - Roteador Semântico EDA AI Minds

## Objetivo
Este módulo realiza o roteamento inteligente de perguntas do usuário, identificando intenções e delegando para agentes especializados via embeddings, busca vetorial e fallback contextual.

## Principais Métodos
- `normalize(question)`: Normaliza a entrada do usuário.
- `embed_question(question)`: Gera embedding vetorial.
- `classify_intent(question)`: Classifica intenção via busca vetorial.
- `fallback_contextual(question)`: Busca resposta contextualizada.
- `route(question)`: Pipeline completo de roteamento.

## Como Usar
```python
from src.router.semantic_router import SemanticRouter
router = SemanticRouter()
resultado = router.route("Detecte fraudes no dataset")
print(resultado)
```

## Expansão Dinâmica
- Novas categorias podem ser inseridas sem downtime usando scripts dedicados.
- Basta rodar `scripts/expand_intent_categories.py` com exemplos reais.

## Auditoria
- Todas decisões e falhas são logadas.
- Auditoria técnica disponível em docs/auditoria/.

## Referências
- Documentação técnica: docs/roteador-semantico.md
- Auditoria: docs/auditoria/auditoria-2025-10-04.md
