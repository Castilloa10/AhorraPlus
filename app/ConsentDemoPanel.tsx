import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

// Rehearsal only: no network, credentials, persistence or bank permissions.
export default function ConsentDemoPanel() {
  const [stage, setStage] = useState<'idle' | 'review' | 'active' | 'disconnect'>('idle');
  const [accepted, setAccepted] = useState(false);
  const [message, setMessage] = useState('');

  function reset(message: string) {
    setStage('idle'); setAccepted(false); setMessage(message);
  }

  function button(label: string, action: () => void, disabled = false) {
    return <Pressable accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled}
      onPress={action} style={[styles.button, disabled && styles.disabled]}>
      <Text style={styles.buttonText}>{label}</Text>
    </Pressable>;
  }

  return <View style={styles.panel}>
    <Text style={styles.badge}>ENSAYO · Sin conexión bancaria</Text>
    <Text accessibilityRole="header" style={styles.heading}>Permiso bancario de prueba</Text>
    <Text style={styles.text}>Revisa cómo sería autorizar y retirar el acceso. Openbank España y Enable Banking son la opción prevista; esta pantalla no contacta con ninguno.</Text>
    <Text style={styles.text}>El ensayo se reinicia al recargar la página. No importa movimientos ni cambia tus saldos.</Text>

    {stage === 'idle' && button('Revisar permiso de prueba', () => {
      setAccepted(false); setMessage(''); setStage('review');
    })}

    {stage === 'review' && <>
      <Text accessibilityRole="header" style={styles.subtitle}>Qué compartirías en una conexión real</Text>
      <Text style={styles.text}>Cuentas que selecciones, identificación de la cuenta y su titular, saldos y movimientos. Se usarían para calcular tu disponible, organizar gastos y presupuestos y preparar análisis financieros.</Text>
      <Text style={styles.text}>El alcance propuesto es solo lectura. No incluye realizar pagos ni transferencias.</Text>
      <Text accessibilityRole="header" style={styles.subtitle}>Quién trataría los datos</Text>
      <Text style={styles.text}>Openbank enviaría los datos a través de Enable Banking y Ahorra+ los guardaría en tu ordenador. En una conexión real la información pasaría por el intermediario.</Text>
      <Text accessibilityRole="header" style={styles.subtitle}>Cuenta, periodo y duración</Text>
      <Text style={styles.text}>En este ensayo: Cuenta ficticia de ensayo. No se solicita historial ni se concede un permiso real. Antes de conectar acordaremos las cuentas, el periodo de movimientos y la duración del acceso; se mostrarán para tu revisión.</Text>
      <Text accessibilityRole="header" style={styles.subtitle}>Cómo retirar el permiso</Text>
      <Text style={styles.text}>La versión real deberá detener la sincronización y solicitar la revocación al proveedor, informando si falla. Podrás revisar el acceso en su portal de consentimientos. Desconectar y borrar movimientos guardados son acciones distintas.</Text>
      <Pressable accessibilityRole="checkbox" accessibilityState={{ checked: accepted }}
        onPress={() => setAccepted(value => !value)} style={styles.checkbox}>
        <Text style={styles.buttonText}>{accepted ? '☑' : '☐'} Entiendo que esto es un ensayo y no autoriza acceso a mi banco.</Text>
      </Pressable>
      {button('Simular autorización', () => { if (accepted) { setStage('active'); setMessage('Permiso ficticio activo únicamente en esta pantalla. No se ha conectado ningún banco.'); } }, !accepted)}
      {button('Cancelar ensayo', () => reset('Ensayo cancelado. No se ha concedido ningún permiso.'))}
    </>}

    {stage === 'active' && <>
      <Text style={styles.subtitle}>Estado: permiso ficticio activo</Text>
      <Text style={styles.text}>Cuenta ficticia de ensayo · Solo lectura simulada · Sin sincronización.</Text>
      {button('Simular desconexión', () => { setStage('disconnect'); setMessage(''); })}
    </>}

    {stage === 'disconnect' && <>
      <Text accessibilityRole="header" style={styles.subtitle}>Confirmar desconexión de prueba</Text>
      <Text style={styles.text}>Se cerrará el permiso ficticio de este ensayo. Tus movimientos DEMO, presupuestos y pagos previstos se conservarán. Esto no revoca ninguna autorización bancaria real.</Text>
      {button('Confirmar desconexión de prueba', () => reset('Ensayo desconectado. Se conservan todos tus datos DEMO. No había ninguna conexión bancaria real.'))}
      {button('Mantener ensayo activo', () => setStage('active'))}
    </>}
    {message !== '' && <Text accessibilityLiveRegion="polite" style={styles.text}>{message}</Text>}
  </View>;
}

const styles = StyleSheet.create({
  panel: { marginTop: 16, padding: 18, gap: 14, borderRadius: 18, backgroundColor: '#fff', borderWidth: 1, borderColor: '#dce5dd' },
  badge: { color: '#644725', fontWeight: '700', alignSelf: 'flex-start', backgroundColor: '#f3e7cf', padding: 8, borderRadius: 8 },
  heading: { fontSize: 20, fontWeight: '800', color: '#172e25' },
  subtitle: { fontSize: 16, fontWeight: '700', color: '#172e25' },
  text: { color: '#4c6258', fontSize: 15, lineHeight: 22 },
  checkbox: { padding: 12, minHeight: 48, borderWidth: 1, borderColor: '#4c6258', borderRadius: 8 },
  button: { backgroundColor: '#e0eee5', borderRadius: 8, padding: 12, minHeight: 44, alignSelf: 'flex-start', maxWidth: '100%' },
  buttonText: { color: '#172e25', fontSize: 15, fontWeight: '600' },
  disabled: { opacity: 0.45 },
});
