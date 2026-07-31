from conftest import login, criar_tecnico, meta_csrf
from database.models.equipamentos import (
    Patrimonio, Computador, Celular, Auditoria, AuditoriaAnexo, ItemAnexo, criar_auditoria
)
from database.models.chamados import Chamado, ChamadoEquipamento
from database.models.usuarios import Setor
from services import equipamento_service


COMPUTADOR_SPEC = {
    'hardware_integro': True, 'bateria_ok': True, 'perifericos_ok': True,
    'limpeza_fisica_ok': True, 'antivirus_ok': True, 'criptografia_ok': True,
    'updates_ok': True, 'softwares_ok': True, 'dominio_ok': True,
    'vpn_ok': True, 'limpeza_disco_ok': True, 'alocacao_ok': True, 'etiqueta_legivel': True,
}


def _criar_computador_com_dependencias(tmp_path, monkeypatch):
    monkeypatch.setattr(equipamento_service, 'UPLOAD_DIR', str(tmp_path))
    setor = Setor.select().first()
    pat = Patrimonio.create(
        codigo_etiqueta='0001', nome_identificador='PC-1',
        tipo='computador', setor=setor, ativo=True
    )
    Computador.create(patrimonio=pat, tag='TAG-1')

    auditoria = criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': 'ok'},
                                COMPUTADOR_SPEC, uploaded_by=1)

    for nome in ('aud_foto.jpg', 'item_foto.jpg'):
        (tmp_path / nome).write_bytes(b'\xff\xd8\xfffake')
    AuditoriaAnexo.create(
        auditoria=auditoria, filename='aud_foto.jpg', stored_filename='aud_foto.jpg',
        mimetype='image/jpeg', filesize=9, uploaded_by=1
    )
    ItemAnexo.create(
        patrimonio=pat, filename='item_foto.jpg', stored_filename='item_foto.jpg',
        mimetype='image/jpeg', filesize=9, uploaded_by=1
    )

    chamado = Chamado.create(
        titulo='Chamado do PC', descricao='x', prioridade='media', funcionario=1
    )
    ChamadoEquipamento.create(
        chamado=chamado, tipo_equipamento='computador', equipamento_id=pat.id
    )
    return pat


def test_deletar_patrimonio_remove_vinculos_e_arquivos(client, tmp_path, monkeypatch):
    pat = _criar_computador_com_dependencias(tmp_path, monkeypatch)
    assert (tmp_path / 'aud_foto.jpg').exists()
    assert (tmp_path / 'item_foto.jpg').exists()

    login(client)
    token = meta_csrf(client)
    resp = client.delete(f'/inventario/computador/{pat.id}/delete', headers={'X-CSRFToken': token})
    assert resp.status_code == 200

    assert Patrimonio.select().count() == 0
    assert ChamadoEquipamento.select().count() == 0
    assert Chamado.select().count() == 1
    assert AuditoriaAnexo.select().count() == 0
    assert ItemAnexo.select().count() == 0
    assert not (tmp_path / 'aud_foto.jpg').exists()
    assert not (tmp_path / 'item_foto.jpg').exists()


def test_deletar_patrimonio_inexistente_retorna_404(client):
    login(client)
    token = meta_csrf(client)
    resp = client.delete('/inventario/computador/999999/delete', headers={'X-CSRFToken': token})
    assert resp.status_code == 404


def test_export_mensal_celulares(client):
    login(client)
    setor = Setor.select().first()
    pat = Patrimonio.create(
        codigo_etiqueta='0002', nome_identificador='iPhone', tipo='celular',
        setor=setor, ativo=True
    )
    Celular.create(patrimonio=pat, modelo='iPhone 12')
    criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': 'Celular OK'},
                    {'apps_ok': True, 'fotos_ok': True, 'informacoes_ok': True,
                     'whatsapp_ok': True, 'avarias_ok': True}, uploaded_by=1)

    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/celular/export/mensal')
    assert resp.status_code == 200
    assert resp.mimetype == 'text/csv'
    assert 'relatorio_mensal' in resp.headers.get('Content-disposition', '')
    assert 'Celular OK' in resp.data.decode('utf-8')
