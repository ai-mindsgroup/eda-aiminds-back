import io
import os
from pathlib import Path

import pandas as pd
import pytest


def write_csv_with_encoding(tmp_path: Path, name: str, encoding: str) -> Path:
    df = pd.DataFrame({
        'texto': ['ação', 'informação', 'coração', 'maçã'],
        'numero': [1, 2, 3, 4],
    })
    csv_path = tmp_path / name
    # Salvar com encoding específico
    df.to_csv(csv_path, index=False, encoding=encoding)
    return csv_path


@pytest.mark.parametrize("encoding", ["utf-8", "latin-1", "cp1252", "utf-16"]) 
def test_dataloader_detects_and_reads_multiple_encodings(tmp_path, encoding):
    from src.data.data_loader import DataLoader

    csv_path = write_csv_with_encoding(tmp_path, f"sample_{encoding.replace('-', '')}.csv", encoding)

    # DataLoader autorizado para testes
    loader = DataLoader(caller_agent="test_system")
    df, info = loader.load_from_file(str(csv_path))

    assert not df.empty
    assert list(df.columns) == ["texto", "numero"]
    assert len(df) == 4
    # encoding reportado deve ser um dos suportados (pode normalizar para lowercase)
    assert info.get("encoding", "").lower() in {"utf-8", "latin-1", "iso-8859-1", "cp1252", "utf-16"}


def test_dataloader_handles_relative_paths(tmp_path, monkeypatch):
    from src.data.data_loader import DataLoader

    # Criar CSV
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    rel_dir = tmp_path / "sub" / "folder"
    rel_dir.mkdir(parents=True)
    csv_path = rel_dir / "relativo.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")

    # Mudar cwd para o diretório pai de 'sub' e usar caminho relativo
    start_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        rel_str = str(Path("sub") / "folder" / "relativo.csv")

        loader = DataLoader(caller_agent="test_system")
        df2, info = loader.load_from_file(rel_str)

        assert len(df2) == 2
        assert info["source_type"] == "file"
        # Deve ser caminho absoluto resolvido
        assert Path(info["source_path"]).is_absolute()
        # Confirma que path existe e aponta para o arquivo criado
        assert Path(info["source_path"]).exists()
    finally:
        os.chdir(start_cwd)
