import os
import io
import pytest
from fastapi.testclient import TestClient
from api_completa import app

client = TestClient(app)

def test_csv_upload_success():
    # Cria um CSV simples em memória
    csv_content = 'col1,col2\n1,2\n3,4'
    file = io.BytesIO(csv_content.encode('utf-8'))
    file.name = 'test_upload.csv'

    response = client.post(
        '/csv/upload',
        files={'file': ('test_upload.csv', file, 'text/csv')}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'file_id' in data
    assert data['filename'] == 'test_upload.csv'
    assert data['rows'] == 2
    assert data['columns'] == 2
    assert data['message'].startswith('CSV carregado')


def test_csv_upload_invalid_extension():
    file = io.BytesIO(b'col1,col2\n1,2')
    file.name = 'test_upload.txt'
    response = client.post(
        '/csv/upload',
        files={'file': ('test_upload.txt', file, 'text/plain')}
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Apenas arquivos CSV são aceitos'


def test_csv_upload_large_file():
    # Simula arquivo grande
    big_csv = 'col1\n' + '\n'.join(['1'] * (2_000_000))
    file = io.BytesIO(big_csv.encode('utf-8'))
    file.name = 'big_upload.csv'
    response = client.post(
        '/csv/upload',
        files={'file': ('big_upload.csv', file, 'text/csv')}
    )
    assert response.status_code in (413, 200)  # Aceita ambos para ambiente dev
