import React, { useState } from 'react';
import { Pressable, Text, View, StyleSheet } from 'react-native';

export default function CategoryEditor({ api, id, category, categories, onSaved }: {
  api: string; id: string; category: string; categories: string[];
  onSaved: () => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [selected, setSelected] = useState(category);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function save() {
    setBusy(true);
    setMessage('');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(api + '/api/v1/demo/movements/category', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ movement_id: id, category: selected }), signal: controller.signal,
      });
      if (!response.ok) throw new Error();
      setEditing(false);
      setMessage('Categoría guardada.');
      await onSaved();
    } catch {
      setMessage('No se pudo confirmar el guardado. Puedes reintentar o actualizar Inicio para comprobar la categoría.');
    } finally {
      clearTimeout(timeout);
      setBusy(false);
    }
  }

  return <View style={styles.container}>
    <Text style={styles.label}>{category}</Text>
    {editing ? <>
      <View style={styles.options}>
        {categories.map(option => <Pressable key={option} accessibilityRole="radio"
          accessibilityState={{ checked: selected === option, disabled: busy }} disabled={busy}
          onPress={() => setSelected(option)} style={[styles.button, selected === option && styles.selected]}>
          <Text style={selected === option ? styles.white : styles.label}>{option}</Text>
        </Pressable>)}
      </View>
      <View style={styles.options}>
        <Pressable accessibilityRole="button" disabled={busy} onPress={save} style={styles.button}>
          <Text>{busy ? 'Guardando…' : 'Guardar categoría'}</Text>
        </Pressable>
        <Pressable accessibilityRole="button" disabled={busy} onPress={() => setEditing(false)} style={styles.button}>
          <Text>Cancelar</Text>
        </Pressable>
      </View>
    </> : <Pressable accessibilityRole="button" disabled={busy}
      onPress={() => { setSelected(category); setMessage(''); setEditing(true); }} style={styles.button}>
      <Text>Cambiar categoría</Text>
    </Pressable>}
    {message !== '' && <Text accessibilityLiveRegion="polite">{message}</Text>}
  </View>;
}

const styles = StyleSheet.create({
  container: { marginTop: 8, gap: 8 },
  options: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  button: { minHeight: 44, padding: 10, borderRadius: 8, backgroundColor: '#e0eee5', justifyContent: 'center', alignSelf: 'flex-start' },
  selected: { backgroundColor: '#174938' },
  label: { color: '#174938' },
  white: { color: '#fff' },
});
