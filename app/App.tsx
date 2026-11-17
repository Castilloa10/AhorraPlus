import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StatusBar, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import demo from './demo.json';
import ImportPanel from './ImportPanel';
import CategoryEditor from './CategoryEditor';
import BudgetPanel, { Budget } from './BudgetPanel';
import PaymentsPanel, { PlannedPayment } from './PaymentsPanel';
import PrivacyPanel from './PrivacyPanel';
import ConsentDemoPanel from './ConsentDemoPanel';

const api = process.env.EXPO_PUBLIC_API_URL?.replace(/\/$/, '');
const euros = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });
const dateLabel = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'long', timeZone: 'UTC' });
const money = (cents: number) => euros.format(cents / 100);
const day = (iso: string) => dateLabel.format(new Date(iso + 'T00:00:00Z'));
type Home = typeof demo & {
  imported_movements?: { id: string; date: string; description: string; cents: number; category?: string }[];
  categories?: string[];
  budget_month?: string;
  budgets?: Budget[];
  planned_payments?: PlannedPayment[];
};

export default function App() {
  const { width } = useWindowDimensions();
  const wide = width >= 760;
  const [data, setData] = useState<Home>(demo);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true);
    setStatus('');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 5000);
    try {
      const response = await fetch(api + '/api/v1/demo/home', { signal: controller.signal });
      if (!response.ok) throw new Error('Respuesta HTTP incorrecta');
      const next: Home = await response.json();
      if (next.demo !== true) throw new Error('Respuesta fuera de DEMO');
      setData(next);
      setStatus('Vista DEMO actualizada.');
    } catch {
      setStatus('No se pudo actualizar el resumen. Los importes visibles pueden estar desactualizados. Pulsa Actualizar para reintentar.');
    } finally {
      clearTimeout(timer);
      setLoading(false);
    }
  }, []);

  useEffect(() => { if (api) void refresh(); }, [refresh]);

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.screen}>
        <StatusBar barStyle="dark-content" />
        <ScrollView contentContainerStyle={styles.scroll}>
          <View style={styles.frame}>
            <View style={styles.header}>
              <Text style={styles.brand}>Ahorra+</Text>
              <Text style={styles.badge}>DEMO · Datos ficticios</Text>
            </View>
            <Text accessibilityRole="header" style={styles.heading}>Inicio</Text>
            <Text style={styles.muted}>Resumen al {day(data.as_of)} de {data.as_of.slice(0, 4)}</Text>

            <View style={styles.hero}>
              <Text style={styles.heroLabel}>Dinero disponible</Text>
              <Text style={[styles.heroValue, wide && styles.heroValueWide]}>{money(data.available_cents)}</Text>
              <Text style={styles.heroLabel}>Saldo menos pagos comprometidos y ahorro protegido</Text>
            </View>

            <View style={[styles.group, wide && styles.row]}>
              <Metric label="Saldo total" cents={data.balance_cents} caption="En tus cuentas propias" />
              <Metric label="Pagos comprometidos" cents={data.committed_cents} caption={'Pendientes hasta el ' + day(data.through)} />
              <Metric label="Ahorro protegido" cents={data.protected_cents} caption="Reservado para tus objetivos" />
            </View>

            <View style={[styles.group, wide && styles.row]}>
              <View style={styles.panel}>
                <Text accessibilityRole="header" style={styles.section}>Pagos comprometidos</Text>
                {data.payments.map((payment, index) => (
                  <View key={index} style={styles.item}>
                    <View style={styles.itemLabel}>
                      <Text style={styles.label}>{payment.name}</Text>
                      <Text style={styles.muted}>{day(payment.date)} · Cargo previsto</Text>
                    </View>
                    <Text style={styles.label}>{money(payment.cents)}</Text>
                  </View>
                ))}
                {data.payments.length === 0 && <Text style={styles.muted}>Sin pagos pendientes en este periodo.</Text>}
              </View>
              <View style={styles.panel}>
                <Text accessibilityRole="header" style={styles.section}>Cuentas propias</Text>
                {data.accounts.map((account, index) => (
                  <View key={index} style={styles.item}>
                    <Text style={[styles.label, styles.itemLabel]}>{account.name}</Text>
                    <Text style={styles.label}>{money(account.cents)}</Text>
                  </View>
                ))}
              </View>
            </View>
            {data.imported_movements && <View style={[styles.panel, { marginTop: 16, flexBasis: 'auto', flexShrink: 0 }]}>
              <Text accessibilityRole="header" style={styles.section}>Movimientos de la cuenta DEMO importada</Text>
              <Text style={styles.muted}>Saldo inicial 0 € · Cargos hasta el {day(data.as_of)} de {data.as_of.slice(0, 4)}</Text>
              {data.imported_movements.length === 0 && <Text style={styles.muted}>Todavía no hay movimientos contabilizados en este periodo.</Text>}
              {data.imported_movements.map(movement => <View key={movement.id} style={styles.item}>
                <View style={styles.itemLabel}>
                  <Text style={styles.label}>{movement.description}</Text>
                  <Text style={styles.muted}>{day(movement.date)} de {movement.date.slice(0, 4)}</Text>
                  {api && movement.category && data.categories && <CategoryEditor
                    api={api} id={movement.id} category={movement.category}
                    categories={data.categories} onSaved={refresh} />}
                </View>
                <Text style={styles.label}>{money(movement.cents)}</Text>
              </View>)}
            </View>}
            {api && data.budget_month && data.budgets && <BudgetPanel
              api={api} month={data.budget_month} budgets={data.budgets} onSaved={refresh} />}
            {api && data.planned_payments && <PaymentsPanel api={api} payments={data.planned_payments} onSaved={refresh} />}
            <ImportPanel api={api} onConfirmed={refresh} />
            <ConsentDemoPanel />
            {api && <PrivacyPanel api={api} onChanged={refresh} />}
            {api && (
              <View style={styles.actions}>
                <Pressable accessibilityRole="button" accessibilityState={{ disabled: loading }}
                  onPress={refresh} disabled={loading} style={styles.button}>
                  {loading ? <ActivityIndicator color="#174938" /> : <Text style={styles.label}>Actualizar desde la API local</Text>}
                </Pressable>
                {status !== '' && <Text accessibilityLiveRegion="polite" style={styles.muted}>{status}</Text>}
              </View>
            )}
          </View>
        </ScrollView>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

function Metric({ label, cents, caption }: { label: string; cents: number; caption: string }) {
  return (
    <View style={styles.panel}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.metric}>{money(cents)}</Text>
      <Text style={styles.muted}>{caption}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#f3f5ef' },
  scroll: { paddingHorizontal: 18, paddingTop: 12, paddingBottom: 36 },
  frame: { width: '100%', maxWidth: 1040, alignSelf: 'center' },
  header: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 8, paddingVertical: 12, marginBottom: 14 },
  brand: { color: '#174938', fontWeight: '800', fontSize: 26, letterSpacing: -0.8 },
  badge: { color: '#644725', backgroundColor: '#f3e7cf', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, fontWeight: '700' },
  heading: { color: '#172e25', fontWeight: '800', fontSize: 38, letterSpacing: -1.5 },
  muted: { color: '#4c6258', fontSize: 14, lineHeight: 20 },
  hero: { backgroundColor: '#174938', borderRadius: 22, padding: 24, gap: 8, marginTop: 20 },
  heroLabel: { color: '#e0f3e7', fontSize: 16, lineHeight: 22 },
  heroValue: { color: '#fff', fontWeight: '800', fontSize: 40, letterSpacing: -1.4 },
  heroValueWide: { fontSize: 56 },
  group: { gap: 12, marginTop: 12 },
  row: { flexDirection: 'row', alignItems: 'stretch' },
  panel: { flexGrow: 1, flexBasis: 0, backgroundColor: '#fff', borderWidth: 1, borderColor: '#dce5dd', borderRadius: 18, padding: 18, gap: 6 },
  label: { color: '#172e25', fontWeight: '700', fontSize: 15 },
  metric: { color: '#174938', fontWeight: '800', fontSize: 28 },
  section: { color: '#172e25', fontWeight: '800', fontSize: 20, marginBottom: 5 },
  item: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 10, borderTopWidth: 1, borderTopColor: '#e7ede8' },
  itemLabel: { flex: 1 },
  actions: { marginTop: 14, gap: 8, alignItems: 'flex-start' },
  button: { minHeight: 44, backgroundColor: '#e0eee5', borderRadius: 10, paddingHorizontal: 14, justifyContent: 'center' },
});
