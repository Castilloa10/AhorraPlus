import React from 'react';
import { Text } from 'react-native';

export default function FilePicker(_props: {
  disabled: boolean;
  onFile: (name: string, content: string) => void;
  onError: (message: string) => void;
}) {
  return <Text>La selección de CSV está disponible en la versión web, también desde Safari en iPhone.</Text>;
}
