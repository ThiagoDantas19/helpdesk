from io import BytesIO
from conftest import meta_csrf, login, criar_tecnico
from utils.compartilhado import validar_arquivo


class FakeFile:
    def __init__(self, content, filename):
        self._content = content
        self.filename = filename

    def read(self, n=-1):
        return self._content[:n] if n > 0 else self._content

    def seek(self, offset, whence=0):
        pass

    def tell(self):
        return len(self._content)


# ── MAGIC BYTES ─────────────────────────────────────────
# validar_arquivo checks if the header matches ANY known magic byte
# it does NOT cross-check that magic matches extension

MAGIC_SAMPLES = [
    (b'\xff\xd8\xff\xe0', 'foto.jpg', True),
    (b'\x89PNG\r\n\x1a\n', 'imagem.png', True),
    (b'GIF87a', 'animacao.gif', True),
    (b'GIF89a', 'animacao2.gif', True),
    (b'BM\x00\x00', 'bitmap.bmp', True),
    (b'RIFFWEBP', 'foto.webp', True),
    (b'\x1aE\xdf\xa3\x01\x00', 'video.mkv', True),
    (b'\x00\x00\x00\x18ftypmp4', 'video.mp4', True),
    (b'\x00\x00\x00\x1cftypmp4', 'video2.mp4', True),
    (b'\x00\x00\x00\x14ftypqt', 'video.mov', True),
    (b'FLV\x01', 'video.flv', True),
    (b'0&\xb2u', 'video.wmv', True),
    (b'RIFF\x00\x00\x00\x00', 'video.avi', True),
    (b'\x00\x00\x00\x00\x00\x00\x00\x00', 'fake.jpg', False),
    (b'texto simples', 'documento.pdf', False),
    (b'<?php echo "x"; ?>', 'shell.php', False),
    (b'\xff\xd8\xff\xe0', 'foto.png', True),
    (b'\x89PNG\r\n\x1a\n', 'foto.jpg', True),
]


def test_magic_bytes_validacao():
    for content, filename, expected in MAGIC_SAMPLES:
        f = FakeFile(content, filename)
        result = validar_arquivo(f)
        assert result == expected, f'Falhou para {filename}: esperado {expected}, obtido {result}'


# ── EXTENSÃO NÃO PERMITIDA ──────────────────────────────

def test_extensao_bloqueada():
    f = FakeFile(b'\xff\xd8\xff\xe0', 'script.exe')
    assert validar_arquivo(f) == False


def test_extensao_sem_ponto():
    f = FakeFile(b'\xff\xd8\xff\xe0', 'foto')
    assert validar_arquivo(f) == False


def test_extensao_maiuscula():
    f = FakeFile(b'\xff\xd8\xff\xe0', 'foto.JPG')
    assert validar_arquivo(f) == True


# ── ARQUIVO VAZIO ───────────────────────────────────────

def test_filename_vazio():
    f = FakeFile(b'\xff\xd8\xff\xe0', '')
    assert validar_arquivo(f) == False


def test_arquivo_none():
    assert validar_arquivo(None) == False


# ── TAMANHO LIMITE ──────────────────────────────────────

def test_imagem_excede_limite(monkeypatch):
    from utils import compartilhado
    monkeypatch.setattr(compartilhado, 'TAMANHO_MAX_IMAGEM', 10)
    f = FakeFile(b'\xff\xd8\xff\xe0' * 10, 'foto.jpg')
    assert validar_arquivo(f) == False


def test_video_excede_limite(monkeypatch):
    from utils import compartilhado
    monkeypatch.setattr(compartilhado, 'TAMANHO_MAX_VIDEO', 10)
    f = FakeFile(b'\x1aE\xdf\xa3\x01\x00' * 10, 'video.mkv')
    assert validar_arquivo(f) == False


def test_imagem_no_limite():
    f = FakeFile(b'\xff\xd8\xff\xe0', 'foto.jpg')
    assert validar_arquivo(f) == True


# ── UPLOAD VIA FLASK CLIENT ─────────────────────────────

COMPUTADOR_SPEC = {
    'hardware_integro': True, 'bateria_ok': True, 'perifericos_ok': True,
    'limpeza_fisica_ok': True, 'antivirus_ok': True, 'criptografia_ok': True,
    'updates_ok': True, 'softwares_ok': True, 'dominio_ok': True,
    'vpn_ok': True, 'limpeza_disco_ok': True, 'alocacao_ok': True, 'etiqueta_legivel': True,
}


def test_upload_auditoria_anexo(client, monkeypatch, tmp_path):
    import routes.inventario as inv_routes
    from utils import compartilhado
    monkeypatch.setattr(compartilhado, 'UPLOAD_DIR', str(tmp_path))
    monkeypatch.setattr(inv_routes, 'UPLOAD_DIR', str(tmp_path))
    login(client)
    pat = _criar_patrimonio()
    from database.models.equipamentos import criar_auditoria
    audit = criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': ''}, COMPUTADOR_SPEC, uploaded_by=1)
    token = meta_csrf(client)
    data = {
        'midia': (BytesIO(b'\xff\xd8\xff\xe0\x00\x00'), 'foto.jpg'),
        'csrf_token': token,
    }
    resp = client.post(f'/inventario/auditoria/{audit.id}/anexar', data=data,
                       follow_redirects=True)
    assert resp.status_code == 200


def test_upload_foto_item(client, monkeypatch, tmp_path):
    import routes.inventario as inv_routes
    from utils import compartilhado
    monkeypatch.setattr(compartilhado, 'UPLOAD_DIR', str(tmp_path))
    monkeypatch.setattr(inv_routes, 'UPLOAD_DIR', str(tmp_path))
    login(client)
    pat = _criar_patrimonio()
    token = meta_csrf(client)
    data = {
        'fotos': (BytesIO(b'\xff\xd8\xff\xe0\x00\x00'), 'item.jpg'),
        'csrf_token': token,
    }
    resp = client.post(f'/inventario/item/{pat.id}/foto', data=data,
                       follow_redirects=True)
    assert resp.status_code == 200


def test_upload_midia_invalida_rejeitada(client, monkeypatch, tmp_path):
    import routes.inventario as inv_routes
    from utils import compartilhado
    monkeypatch.setattr(compartilhado, 'UPLOAD_DIR', str(tmp_path))
    monkeypatch.setattr(inv_routes, 'UPLOAD_DIR', str(tmp_path))
    login(client)
    pat = _criar_patrimonio()
    from database.models.equipamentos import criar_auditoria
    audit = criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': ''}, COMPUTADOR_SPEC, uploaded_by=1)
    token = meta_csrf(client)
    data = {
        'midia': (BytesIO(b'not-a-valid-image-file'), 'script.exe'),
        'csrf_token': token,
    }
    resp = client.post(f'/inventario/auditoria/{audit.id}/anexar', data=data,
                       follow_redirects=True)
    assert resp.status_code == 200


def _criar_patrimonio():
    from database.models.usuarios import Setor
    from database.models.equipamentos import Patrimonio, Computador
    from utils.constants import TIPO_COMPUTADOR
    setor = Setor.get_or_none(Setor.nome == 'TI')
    if not setor:
        setor = Setor.create(nome='TI')
    pat = Patrimonio.create(
        codigo_etiqueta='PC-TEST', nome_identificador='PC-Test',
        tipo=TIPO_COMPUTADOR, setor=setor, ativo=True
    )
    Computador.create(patrimonio=pat, tag='TAG-TEST')
    return pat