import os
import uuid
import csv
from io import StringIO
from flask import Response
from flask_login import current_user
from utils.constants import UPLOAD_DIR
from database.models.chamados import ChamadoAnexo
from database.models.equipamentos import Patrimonio, Auditoria

EXTENSOES_PERMITIDAS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
    '.mp4', '.webm', '.avi', '.mkv', '.mov', '.wmv', '.flv'
}

EXTENSOES_IMAGEM = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
EXTENSOES_VIDEO = {'.mp4', '.webm', '.avi', '.mkv', '.mov', '.wmv', '.flv'}

TAMANHO_MAX_IMAGEM = 10 * 1024 * 1024
TAMANHO_MAX_VIDEO = 50 * 1024 * 1024

MAGIC_BYTES = [
    (b'\xff\xd8\xff', {'jpg', 'jpeg'}),
    (b'\x89PNG\r\n\x1a\n', {'png'}),
    (b'GIF87a', {'gif'}),
    (b'GIF89a', {'gif'}),
    (b'BM', {'bmp'}),
    (b'\x1aE\xdf\xa3', {'webm', 'mkv'}),
    (b'0&\xb2u', {'wmv'}),
    (b'FLV', {'flv'}),
    (b'RIFFWEBP', {'webp'}),
    (b'RIFF', {'avi'}),
    (b'\x00\x00\x00\x18ftyp', {'mp4', 'mov'}),
    (b'\x00\x00\x00\x1cftyp', {'mp4'}),
    (b'\x00\x00\x00\x14ftyp', {'mov'}),
]


def _magias_do_arquivo(f):
    header = f.read(16)
    f.seek(0)
    for magic, _exts in MAGIC_BYTES:
        if header.startswith(magic):
            return True
    return False


def validar_arquivo(f):
    if not f or not f.filename:
        return False
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in EXTENSOES_PERMITIDAS:
        return False
    limite = TAMANHO_MAX_IMAGEM if ext in EXTENSOES_IMAGEM else TAMANHO_MAX_VIDEO
    f.seek(0, os.SEEK_END)
    if f.tell() > limite:
        return False
    f.seek(0)
    if not _magias_do_arquivo(f):
        return False
    return True


def salvar_midia(arquivo):
    ext = os.path.splitext(arquivo.filename)[1].lower()
    stored = f'{uuid.uuid4().hex}{ext}'
    caminho = os.path.join(UPLOAD_DIR, stored)
    arquivo.save(caminho)
    return stored


def salvar_anexos_chamado(chamado, arquivos):
    for f in arquivos:
        if not validar_arquivo(f):
            continue
        stored = salvar_midia(f)
        ChamadoAnexo.create(
            chamado=chamado,
            filename=f.filename,
            stored_filename=stored,
            mimetype=f.content_type or 'application/octet-stream',
            filesize=os.path.getsize(os.path.join(UPLOAD_DIR, stored)),
            uploaded_by=current_user.id
        )


def export_auditoria_csv(patrimonio_id, header_row, row_generator, filename_prefix='auditoria', auditorias_query=None):
    patrimonio = Patrimonio.get_by_id(patrimonio_id)
    if auditorias_query is None:
        auditorias = [(a, []) for a in (Auditoria
                      .select()
                      .where(Auditoria.patrimonio == patrimonio)
                      .order_by(Auditoria.data_auditoria.desc()))]
    else:
        auditorias = auditorias_query
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(header_row)
    for auditoria, detalhes in auditorias:
        cw.writerow(row_generator(auditoria, detalhes[0] if detalhes else None))
    response = Response(si.getvalue(), mimetype='text/csv')
    response.headers['Content-disposition'] = (
        f'attachment; filename={filename_prefix}_{patrimonio.codigo_etiqueta}.csv'
    )
    return response
