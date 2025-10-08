"""Testes unitários para parsing defensivo de embeddings.

Este módulo testa a função parse_embedding_from_api para garantir
que embeddings retornados como strings pela API Supabase sejam
corretamente convertidos para listas de floats.
"""
import pytest
from src.embeddings.vector_store import parse_embedding_from_api, VECTOR_DIMENSIONS


def test_parse_embedding_from_list():
    """Testa parsing quando embedding já é uma lista."""
    embedding = [0.1, 0.2, 0.3] + [0.0] * (VECTOR_DIMENSIONS - 3)
    result = parse_embedding_from_api(embedding)
    assert isinstance(result, list)
    assert len(result) == VECTOR_DIMENSIONS
    assert all(isinstance(x, float) for x in result)
    assert result[:3] == [0.1, 0.2, 0.3]


def test_parse_embedding_from_string():
    """Testa parsing quando embedding é uma string."""
    embedding = "[" + ",".join(["0.1"] * VECTOR_DIMENSIONS) + "]"
    result = parse_embedding_from_api(embedding)
    assert isinstance(result, list)
    assert len(result) == VECTOR_DIMENSIONS
    assert all(isinstance(x, float) for x in result)
    assert all(x == 0.1 for x in result)


def test_parse_embedding_from_string_with_spaces():
    """Testa parsing quando embedding é uma string com espaços."""
    embedding = "[" + ", ".join(["0.1"] * VECTOR_DIMENSIONS) + "]"
    result = parse_embedding_from_api(embedding)
    assert isinstance(result, list)
    assert len(result) == VECTOR_DIMENSIONS
    assert all(isinstance(x, float) for x in result)
    assert all(x == 0.1 for x in result)


def test_parse_embedding_wrong_dimensions():
    """Testa erro quando embedding tem dimensões incorretas."""
    embedding = [0.1, 0.2, 0.3]  # Apenas 3 dimensões
    with pytest.raises(ValueError, match="dimensões"):
        parse_embedding_from_api(embedding)


def test_parse_embedding_none():
    """Testa erro quando embedding é None."""
    with pytest.raises(ValueError, match="None"):
        parse_embedding_from_api(None)


def test_parse_embedding_invalid_string():
    """Testa erro quando embedding é uma string inválida."""
    with pytest.raises(ValueError, match="parsear"):
        parse_embedding_from_api("invalid string")


def test_parse_embedding_unsupported_type():
    """Testa erro quando embedding é de tipo não suportado."""
    with pytest.raises(ValueError, match="não suportado"):
        parse_embedding_from_api({"embedding": [0.1, 0.2]})


def test_parse_embedding_non_numeric():
    """Testa erro quando embedding contém valores não numéricos."""
    embedding = ["a", "b", "c"] + [0.0] * (VECTOR_DIMENSIONS - 3)
    with pytest.raises(ValueError, match="converter elementos"):
        parse_embedding_from_api(embedding)


def test_parse_embedding_from_json_string():
    """Testa parsing quando embedding é uma string JSON."""
    import json
    embedding_list = [0.1] * VECTOR_DIMENSIONS
    embedding_json = json.dumps(embedding_list)
    result = parse_embedding_from_api(embedding_json)
    assert isinstance(result, list)
    assert len(result) == VECTOR_DIMENSIONS
    assert all(isinstance(x, float) for x in result)
    assert all(x == 0.1 for x in result)


def test_parse_embedding_with_integers():
    """Testa parsing quando embedding contém integers."""
    embedding = [1, 2, 3] + [0] * (VECTOR_DIMENSIONS - 3)
    result = parse_embedding_from_api(embedding)
    assert isinstance(result, list)
    assert len(result) == VECTOR_DIMENSIONS
    assert all(isinstance(x, float) for x in result)
    assert result[:3] == [1.0, 2.0, 3.0]


def test_parse_embedding_realistic_scenario():
    """Testa parsing em um cenário realista com embedding do Supabase."""
    # Simula o retorno da API Supabase (string)
    embedding_from_api = "[" + ",".join([str(i * 0.001) for i in range(VECTOR_DIMENSIONS)]) + "]"
    
    result = parse_embedding_from_api(embedding_from_api)
    
    assert isinstance(result, list)
    assert len(result) == VECTOR_DIMENSIONS
    assert all(isinstance(x, float) for x in result)
    # Verificar primeiros valores
    assert abs(result[0] - 0.0) < 1e-6
    assert abs(result[1] - 0.001) < 1e-6
    assert abs(result[10] - 0.010) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
