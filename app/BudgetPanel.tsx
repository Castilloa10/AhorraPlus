import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

export type Budget = { category: string; limit_cents: number | null; spent_cents: number; remaining_cents: number | null };
const euros = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });
const money = (cents: number) => euros.format(cents / 100);

function BudgetRow({ budget, api, month, onSaved }: {
  budget: Budget; api: string; month: string; onSaved: () => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [amount, setAmount] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function save() {
    const normalized = amount.trim().replace(',', '.');
    if (!/^\d+(\.\d{1,2})?$/.test(normalized) || Number(normalized) > 1000000) {
      setMessage('Introduce un importe entre 0 y 1.000.000, con un máximo de dos decimales y sin separador de miles.');
      return;
    }
    setBusy(true);
    setMessage('');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(api + '/api/v1/demo/budgets', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ month, category: budget.category, limit_cents: Math.round(Number(normalized) * 100) }),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error();
      setEditing(false);
      setMessage('Presupuesto guardado.');
      await onSaved();
    } catch {
      setMessage('No se pudo confirmar el guardado. Puedes actualizar Inicio o reintentar.');
    } finally {
      clearTimeout(timeout);
      setBusy(false);
    }
  }

  return <View style={styles.row}>
    <Text style={styles.label}>{budget.category}</Text>
    <Text>Gastado {money(budget.spent_cents)}</Text>
    <Text>{budget.limit_cents === null ? 'Sin presupuesto' : 'Límite mensual ' + money(budget.limit_cents)}</Text>
    {budget.remaining_cents !== null && <Text style={budget.remaining_cents < 0 ? styles.exceeded : styles.label}>
      {budget.remaining_cents < 0 ? 'Excedido en ' + money(-budget.remaining_cents) : 'Restante ' + money(budget.remaining_cents)}
    </Text>}
    {editing ? <View style={styles.controls}>
      <TextInput accessibilityLabel={'Límite mensual en euros para ' + budget.category}
        value={amount} onChangeText={setAmount} editable={!busy} keyboardType="decimal-pad"
        placeholder="Importe en euros" style={styles.input} />
      <Pressable accessibilityRole="button" disabled={busy} onPress={save} style={styles.button}>
        <Text>{busy ? 'Guardando…' : 'Guardar presupuesto'}</Text>
      </Pressable>
      <Pressable accessibilityRole="button" disabled={busy} onPress={() => setEditing(false)} style={styles.button}>
        <Text>Cancelar</Text>
      </Pressable>
    </View> : <Pressable accessibilityRole="button" disabled={busy} style={styles.button} onPress={() => {
      setAmount(budget.limit_cents === null ? '' : (budget.limit_cents / 100).toFixed(2).replace('.', ','));
      setMessage(''); setEditing(true);
    }}><Text>{budget.limit_cents === null ? 'Fijar presupuesto' : 'Editar presupuesto'}</Text></Pressable>}
    {message !== '' && <Text accessibilityLiveRegion="polite">{message}</Text>}
  </View>;
}

export default function BudgetPanel({ budgets, month, api, onSaved }: {
  budgets: Budget[]; month: string; api: string; onSaved: () => Promise<void>;
}) {
  const label = new Intl.DateTimeFormat('es-ES', { month: 'long', year: 'numeric', timeZone: 'UTC' })
    .format(new Date(month + '-01T00:00:00Z'));
  return <View style={styles.panel}>
    <Text accessibilityRole="header" style={styles.heading}>Presupuestos · {label}</Text>
    <Text>Cuenta DEMO importada · Gasto neto registrado hasta la fecha del resumen.</Text>
    {budgets.map(budget => <BudgetRow key={month + budget.category} budget={budget} month={month} api={api} onSaved={onSaved} />)}
  </View>;
}

const styles = StyleSheet.create({
  panel: { marginTop: 16, padding: 18, gap: 12, borderRadius: 18, backgroundColor: '#fff' },
  heading: { fontSize: 20, fontWeight: '800', color: '#172e25' },
  row: { borderTopWidth: 1, borderTopColor: '#e7ede8', paddingVertical: 12, gap: 8 },
  label: { fontWeight: '700', color: '#174938' },
  exceeded: { fontWeight: '700', color: '#9b2626' },
  controls: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#4c6258', borderRadius: 8, padding: 10, minHeight: 44, minWidth: 150, maxWidth: '100%', color: '#172e25' },
  button: { backgroundColor: '#e0eee5', borderRadius: 8, padding: 12, minHeight: 44, alignSelf: 'flex-start', justifyContent: 'center' },
});
