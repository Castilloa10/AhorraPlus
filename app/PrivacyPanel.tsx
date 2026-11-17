import React, { useState } from 'react';
import { Pressable, Text, TextInput, View, StyleSheet } from 'react-native';

export default function PrivacyPanel({ api, onChanged }: { api: string; onChanged: () => Promise<void> }) {
  const [confirmation, setConfirmation] = useState('');
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function perform(action: string) {
    setBusy(true); setMessage('');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(api + '/api/v1/demo/privacy/' + action, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmation }), signal: controller.signal,
      });
      if (!response.ok) throw new Error();
      setMessage(action === 'disconnect'
        ? 'Claves y autorización locales de prueba eliminadas.'
        : 'Movimientos importados y sus categorías eliminados. Puedes volver a importar la muestra.');
      setEditing(false); setConfirmation('');
      await onChanged();
    } catch {
      setMessage('No se pudo confirmar la operación. Actualiza Inicio antes de reintentar.');
    } finally { clearTimeout(timer); setBusy(false); }
  }

  return <View style={styles.panel}>
    <Text accessibilityRole="header" style={styles.heading}>Privacidad · DEMO local</Text>
    <Text>La base de datos se protege con el usuario de Windows al abrirla con esta versión. El modo actual es simulación bancaria.</Text>
    <Pressable accessibilityRole="button" disabled={busy} onPress={() => perform('disconnect')} style={styles.button}>
      <Text>Desconectar autorización local de prueba</Text>
    </Pressable>
    <Text>La desconexión local borra las claves y la sesión de prueba. La revocación de un permiso bancario real deberá hacerse mediante su proveedor cuando se implemente esa conexión.</Text>
    {editing ? <>
      <Text>Se eliminarán los movimientos importados, sus categorías manuales y el historial de importaciones de la cuenta DEMO. Los presupuestos y pagos previstos se conservan. Escribe BORRAR DEMO para confirmar.</Text>
      <TextInput accessibilityLabel="Confirmación de borrado" value={confirmation} onChangeText={setConfirmation}
        editable={!busy} style={styles.input} />
      <Pressable accessibilityRole="button" disabled={busy || confirmation !== 'BORRAR DEMO'}
        accessibilityState={{ disabled: busy || confirmation !== 'BORRAR DEMO' }}
        onPress={() => perform('delete-imported')} style={styles.button}><Text>Confirmar borrado</Text></Pressable>
      <Pressable accessibilityRole="button" disabled={busy} onPress={() => { setEditing(false); setConfirmation(''); }}
        style={styles.button}><Text>Cancelar</Text></Pressable>
    </> : <Pressable accessibilityRole="button" disabled={busy} onPress={() => setEditing(true)} style={styles.button}>
      <Text>Borrar datos importados de prueba</Text>
    </Pressable>}
    {message !== '' && <Text accessibilityLiveRegion="polite">{message}</Text>}
  </View>;
}

const styles = StyleSheet.create({
  panel: { marginTop: 16, padding: 18, gap: 12, borderRadius: 18, backgroundColor: '#fff' },
  heading: { fontSize: 20, fontWeight: '800', color: '#172e25' },
  input: { borderWidth: 1, borderColor: '#4c6258', borderRadius: 8, padding: 10, minHeight: 44 },
  button: { backgroundColor: '#e0eee5', borderRadius: 8, padding: 12, minHeight: 44, alignSelf: 'flex-start' },
});
