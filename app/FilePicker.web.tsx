import React from 'react';

export default function FilePicker({ disabled, onFile, onError }: {
  disabled: boolean;
  onFile: (name: string, content: string) => void;
  onError: (message: string) => void;
}) {
  return <input aria-label="Seleccionar CSV de prueba" type="file" accept=".csv,text/csv" disabled={disabled}
    style={{ maxWidth: '100%', padding: 12, fontSize: 16 }}
    onChange={async event => {
      const file = event.target.files?.[0];
      event.target.value = '';
      if (!file) return;
      if (file.size > 500000) {
        onError('El archivo supera el límite de 500 KB.');
        return;
      }
      try {
        onFile(file.name, await file.text());
      } catch {
        onError('No se pudo leer el archivo.');
      }
    }} />;
}
