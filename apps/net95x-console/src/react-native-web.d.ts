// Browser-only type surface for the React Native Web primitives used by App.tsx.
// The Vite alias resolves these imports to react-native-web at runtime.
declare module 'react-native' {
  import type { ComponentType, ReactNode } from 'react';

  type Style = Record<string, string | number | undefined>;
  type StyleValue = Style | false | null | undefined | StyleValue[];
  type BaseProps = { children?: ReactNode; style?: StyleValue };

  export const View: ComponentType<BaseProps>;
  export const Text: ComponentType<BaseProps>;
  export const ScrollView: ComponentType<{ children?: ReactNode; contentContainerStyle?: StyleValue }>;
  export const Pressable: ComponentType<{ children?: ReactNode;
    accessibilityRole?: string;
    accessibilityState?: { disabled?: boolean };
    disabled?: boolean;
    onPress?: () => void;
    style?: StyleValue | ((state: { pressed: boolean }) => StyleValue);
  }>;
  export const StyleSheet: { create<T extends Record<string, Style>>(styles: T): T };
  export function useWindowDimensions(): { width: number; height: number; scale: number; fontScale: number };
}
