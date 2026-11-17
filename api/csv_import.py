from api.storage import connect
"""Local DEMO CSV preview and atomic confirmation. Run with python -m api.csv_import."""
import argparse
import csv
import hashlib
import io
import json
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


def preview(content: str):
    reader = csv.DictReader(io.StringIO(content.lstrip('\ufeff')))
    required = ['id', 'fecha', 'concepto', 'importe']
    if reader.fieldnames != required:
        raise ValueError('Cabecera esperada: id,fecha,concepto,importe')
    rows, errors, seen = [], [], set()
    for number, row in enumerate(reader, 2):
        try:
            if None in row or any(value is None for value in row.values()):
                raise ValueError('Número de columnas incorrecto')
            identifier = row['id'].strip()
            description = row['concepto'].strip()
            if not identifier or not description:
                raise ValueError('ID y concepto obligatorios')
            if identifier in seen:
                raise ValueError('ID repetido en el archivo')
            charged = date.fromisoformat(row['fecha']).isoformat()
            amount = Decimal(row['importe'])
            if not amount.is_finite() or abs(amount) > Decimal('1000000000'):
                raise ValueError('Importe fuera de rango')
            cents = amount * 100
            if cents != cents.to_integral_value():
                raise ValueError('El importe admite como máximo dos decimales')
            rows.append((identifier, charged, description, int(cents)))
            seen.add(identifier)
        except (ValueError, InvalidOperation) as error:
            errors.append(f'Fila {number}: {error}')
    if not rows and not errors:
        errors.append('El archivo está vacío')
    return rows, errors


def confirm(connection, account, content):
    rows, errors = preview(content)
    if errors:
        raise ValueError('\n'.join(errors))
    fingerprint = hashlib.sha256(json.dumps(rows, ensure_ascii=True).encode()).hexdigest()
    connection.execute('CREATE TABLE IF NOT EXISTS movements (account TEXT, external_id TEXT, charged_on TEXT, description TEXT, cents INTEGER, PRIMARY KEY(account, external_id))')
    connection.execute('CREATE TABLE IF NOT EXISTS batches (account TEXT, fingerprint TEXT, PRIMARY KEY(account, fingerprint))')
    with connection:
        connection.execute('BEGIN IMMEDIATE')
        if connection.execute('SELECT 1 FROM batches WHERE account=? AND fingerprint=?', (account, fingerprint)).fetchone():
            return 0
        inserted = 0
        for identifier, charged, description, cents in rows:
            existing = connection.execute('SELECT charged_on, description, cents FROM movements WHERE account=? AND external_id=?', (account, identifier)).fetchone()
            if existing is not None:
                if existing != (charged, description, cents):
                    raise ValueError(f'El ID {identifier} ya existe con otros datos. Revisa el archivo.')
                continue
            connection.execute('INSERT INTO movements VALUES (?, ?, ?, ?, ?)', (account, identifier, charged, description, cents))
            inserted += 1
        connection.execute('INSERT INTO batches VALUES (?, ?)', (account, fingerprint))
        return inserted


def main():
    parser = argparse.ArgumentParser(description='Importación local DEMO en EUR')
    parser.add_argument('file', type=Path)
    parser.add_argument('--confirmar', action='store_true')
    args = parser.parse_args()
    content = args.file.read_text(encoding='utf-8-sig')
    rows, errors = preview(content)
    print('DEMO · Vista previa · Cuenta de prueba · EUR')
    for identifier, charged, description, cents in rows:
        print(f'{identifier} | {charged} | {description} | {Decimal(cents) / 100:.2f} EUR')
    if errors:
        parser.exit(1, '\n'.join(errors) + '\n')
    if args.confirmar:
        connection = connect(Path(__file__).resolve().parents[1] / 'demo-import.sqlite3')
        try:
            print(f'Movimientos nuevos: {confirm(connection, "demo", content)}')
        except ValueError as error:
            parser.exit(1, str(error) + '\n')
        finally:
            connection.close()
    else:
        print('Para guardar este lote, repite con --confirmar.')


if __name__ == '__main__':
    main()

