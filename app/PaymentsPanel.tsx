import React, { useState } from 'react';
import { Pressable, Text, TextInput, View, StyleSheet } from 'react-native';

export type PlannedPayment = { id: string; name: string; date: string; cents: number; kind: string };
const currency = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });

export default function PaymentsPanel({ payments, api, onSaved }: {
  payments: PlannedPayment[]; api: string; onSaved: () => Promise<void>;
}) {
  const [draft, setDraft] = useState<PlannedPayment | null>(null);
  const [amount, setAmount] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  function edit(payment: PlannedPayment) {
    setDraft({ ...payment });
    setAmount(payment.cents ? (payment.cents / 100).toFixed(2).replace('.', ',') : '');
    setMessage('');
  }

  async function save() {
    if (!draft) return;
    const normalized = amount.trim().replace(',', '.');
    if (!draft.name.trim() || !/^\d{4}-\d{2}-\d{2}$/.test(draft.date) ||
      !/^\d+(\.\d{1,2})?$/.test(normalized) || Number(normalized) <= 0 || Number(normalized) > 1000000) {
      setMessage('Completa el nombre, la fecha AAAA-MM-DD y un importe positivo de hasta 1.000.000 €, sin separador de miles.');
      return;
    }
    setBusy(true);
    setMessage('');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(api + '/api/v1/demo/payments', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...draft, cents: Math.round(Number(normalized) * 100) }),
        signal: controller.signal,
      });
      if (!response.ok) {
        setMessage('No se pudo guardar. Comprueba que la fecha existe y que los datos son válidos.');
        return;
      }
      setDraft(null);
      setMessage('Pago guardado.');
      await onSaved();
    } catch {
      setMessage('No se pudo confirmar el guardado. Puedes reintentar con este mismo formulario.');
    } finally {
      clearTimeout(timer); setBusy(false);
    }
  }

  return <View style={styles.panel}>
    <Text accessibilityRole="header" style={styles.heading}>Gastos fijos e irregulares</Text>
    <Text>Cada entrada representa un cargo pendiente. Los vencidos y los previstos hasta fin de mes se incluyen en pagos comprometidos.</Text>
    {payments.map(payment => <View key={payment.id} style={styles.row}>
      <Text style={styles.label}>{payment.name} · {currency.format(payment.cents / 100)}</Text>
      <Text>{payment.kind} · Cargo previsto {payment.date}</Text>
      <Pressable accessibilityRole="button" disabled={busy || draft !== null}
        onPress={() => edit(payment)} style={styles.button}><Text>Editar {payment.name}</Text></Pressable>
    </View>)}
    {draft ? <View style={styles.form}>
      <Text style={styles.label}>Nombre</Text>
      <TextInput accessibilityLabel="Nombre del gasto" editable={!busy} maxLength={120} style={styles.input}
        value={draft.name} onChangeText={name => setDraft({ ...draft, name })} />
      <Text style={styles.label}>Importe en euros</Text>
      <TextInput accessibilityLabel="Importe en euros" editable={!busy} keyboardType="decimal-pad"
        style={styles.input} value={amount} onChangeText={setAmount} />
      <Text style={styles.label}>Fecha prevista de cargo · AAAA-MM-DD</Text>
      <TextInput accessibilityLabel="Fecha prevista de cargo" editable={!busy} style={styles.input}
        value={draft.date} placeholder="2026-11-25" onChangeText={date => setDraft({ ...draft, date })} />
      <View style={styles.options}>{['Fijo', 'Irregular'].map(kind => <Pressable key={kind}
        accessibilityRole="radio" accessibilityState={{ checked: draft.kind === kind, disabled: busy }}
        disabled={busy} onPress={() => setDraft({ ...draft, kind })} style={styles.button}>
        <Text>{draft.kind === kind ? '● ' : '○ '}{kind}</Text>
      </Pressable>)}</View>
      <View style={styles.options}>
        <Pressable accessibilityRole="button" disabled={busy} onPress={save} style={styles.button}>
          <Text>{busy ? 'Guardando…' : 'Guardar pago'}</Text>
        </Pressable>
        <Pressable accessibilityRole="button" disabled={busy} onPress={() => { setDraft(null); setMessage(''); }} style={styles.button}>
          <Text>Cancelar</Text>
        </Pressable>
      </View>
    </View> : <Pressable accessibilityRole="button" disabled={busy} style={styles.button} onPress={() => edit({
      id: 'payment-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2),
      name: '', date: '', cents: 0, kind: 'Fijo',
    })}><Text>Añadir gasto</Text></Pressable>}
    {message !== '' && <Text accessibilityLiveRegion="polite">{message}</Text>}
  </View>;
}

const styles = StyleSheet.create({
  panel: { marginTop: 16, padding: 18, gap: 12, borderRadius: 18, backgroundColor: '#fff' },
  heading: { fontSize: 20, fontWeight: '800', color: '#172e25' },
  label: { fontWeight: '700', color: '#174938' },
  row: { borderTopWidth: 1, borderTopColor: '#e7ede8', paddingVertical: 12, gap: 8 },
  form: { gap: 10 },
  options: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  input: { borderWidth: 1, borderColor: '#4c6258', borderRadius: 8, padding: 10, minHeight: 44, color: '#172e25' },
  button: { backgroundColor: '#e0eee5', borderRadius: 8, padding: 12, minHeight: 44, alignSelf: 'flex-start', justifyContent: 'center' },
});
