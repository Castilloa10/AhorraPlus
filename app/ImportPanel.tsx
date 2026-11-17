import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import FilePicker from './FilePicker';

type Preview = { rows: [string, string, string, number][]; errors: string[] };
const euros = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });

export default function ImportPanel({ api, onConfirmed }: { api?: string; onConfirmed: () => Promise<void> }) {
  const [content, setContent] = useState('');
  const [name, setName] = useState('');
  const [preview, setPreview] = useState<Preview | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [confirmed, setConfirmed] = useState(false);

  async function request(action: string, text: string) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(api + '/api/v1/demo/import/' + action, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text }), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Revisa el formato y el tamaño del archivo.');
      return result;
    } finally {
      clearTimeout(timeout);
    }
  }

  function failure(error: unknown) {
    if (error instanceof TypeError) {
      setMessage('No se pudo conectar con la API local. Comprueba que está en marcha y que la dirección y el puerto coinciden con las instrucciones del README.');
      return;
    }
    setMessage(error instanceof Error && error.name !== 'AbortError'
      ? error.message : 'La solicitud ha tardado demasiado. Puedes reintentar sin duplicar movimientos.');
  }

  async function select(filename: string, text: string) {
    setBusy(true);
    setPreview(null);
    setConfirmed(false);
    setMessage('');
    setName(filename);
    setContent(text);
    try {
      setPreview(await request('preview', text));
    } catch (error) {
      failure(error);
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    setBusy(true);
    setMessage('');
    try {
      const result = await request('confirm', content);
      setMessage(result.inserted === 0 ? 'Este lote ya estaba guardado. Se han añadido 0 movimientos.'
        : 'Importación confirmada. Movimientos nuevos: ' + result.inserted);
      setConfirmed(true);
      await onConfirmed();
    } catch (error) {
      failure(error);
    } finally {
      setBusy(false);
    }
  }

  async function simulateBank() {
    setBusy(true);
    setPreview(null);
    setName('');
    setContent('');
    setConfirmed(false);
    setMessage('');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(api + '/api/v1/demo/bank-simulation', { signal: controller.signal });
      if (!response.ok) throw new Error('No se pudo cargar la simulación.');
      const result = await response.json();
      if (result.demo !== true || typeof result.content !== 'string') throw new Error('Respuesta de simulación no válida.');
      await select('Simulación bancaria local · Datos ficticios', result.content);
    } catch (error) {
      failure(error);
    } finally {
      clearTimeout(timer);
      setBusy(false);
    }
  }

  return <View style={styles.panel}>
    <Text accessibilityRole="header" style={styles.heading}>Importar movimientos DEMO</Text>
    <Text>Selecciona un CSV ficticio para la cuenta de prueba, en euros.</Text>
    <Text>Columnas en orden: id, fecha, concepto, importe. Fecha AAAA-MM-DD e importe con punto decimal.</Text>
    {api ? <FilePicker disabled={busy} onFile={select} onError={text => {
      setPreview(null); setMessage(text); setName(''); setContent(''); setConfirmed(false);
    }} /> : <Text>Inicia la API y configura EXPO_PUBLIC_API_URL siguiendo el README para importar.</Text>}
    {api && <>
      <Text style={styles.heading}>Simulación bancaria local</Text>
      <Text>Prueba con dos movimientos ficticios de −30 € y +10 €. Al confirmar, se añadirán a la cuenta DEMO importada. Un tercer movimiento pendiente queda fuera del lote.</Text>
      <Pressable accessibilityRole="button" disabled={busy} accessibilityState={{ disabled: busy }}
        onPress={simulateBank} style={styles.button}><Text style={styles.buttonText}>Cargar simulación bancaria</Text></Pressable>
    </>}
    {busy && <ActivityIndicator accessibilityLabel="Procesando archivo" />}
    {name !== '' && <Text style={styles.heading}>{name}</Text>}
    {preview && <>
      <Text>{preview.rows.length} movimientos · Vista previa</Text>
      {preview.rows.map(([id, date, description, cents]) => <View key={id} style={styles.row}>
        <Text style={styles.description}>{date} · {description}</Text>
        <Text>{euros.format(cents / 100)}</Text>
      </View>)}
      {preview.errors.map((error, index) => <Text key={index} style={styles.error}>{error}</Text>)}
      {preview.errors.length === 0 && !confirmed && <Pressable accessibilityRole="button"
        disabled={busy} accessibilityState={{ disabled: busy }} onPress={save} style={styles.button}>
        <Text style={styles.buttonText}>Confirmar importación</Text>
      </Pressable>}
      {!confirmed && <Pressable accessibilityRole="button" disabled={busy} style={styles.button}
        onPress={() => { setPreview(null); setContent(''); setName(''); setMessage('Vista previa cancelada.'); }}>
        <Text style={styles.buttonText}>Cancelar importación</Text>
      </Pressable>}
    </>}
    {message !== '' && <Text accessibilityLiveRegion="polite">{message}</Text>}
    <Text>Los movimientos se guardan en la cuenta DEMO importada, con saldo inicial de 0 €. Inicio suma los cargos hasta su fecha de corte.</Text>
  </View>;
}

const styles = StyleSheet.create({
  panel: { marginTop: 16, padding: 18, gap: 12, borderRadius: 18, backgroundColor: '#fff' },
  heading: { fontSize: 18, fontWeight: '700', color: '#174938' },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#e7ede8' },
  description: { flexGrow: 1, flexShrink: 1 },
  error: { color: '#9b2626' },
  button: { backgroundColor: '#174938', padding: 14, borderRadius: 10, alignSelf: 'flex-start' },
  buttonText: { color: '#fff', fontWeight: '700' },
});
