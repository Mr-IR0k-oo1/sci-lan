import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { ComponentSelection } from '../types';

interface SelectionContextValue {
  selected: ComponentSelection | null;
  select: (selection: ComponentSelection | null) => void;
  lineToolActive: boolean;
  setLineToolActive: (active: boolean) => void;
  lineFrom: string | null;
  setLineFrom: (busId: string | null) => void;
}

const SelectionContext = createContext<SelectionContextValue | null>(null);

export function SelectionProvider({ children }: { children: ReactNode }) {
  const [selected, setSelected] = useState<ComponentSelection | null>(null);
  const [lineToolActive, setLineToolActive] = useState(false);
  const [lineFrom, setLineFrom] = useState<string | null>(null);

  const value = useMemo<SelectionContextValue>(
    () => ({
      selected,
      select: setSelected,
      lineToolActive,
      setLineToolActive,
      lineFrom,
      setLineFrom,
    }),
    [selected, lineToolActive, lineFrom],
  );

  return <SelectionContext.Provider value={value}>{children}</SelectionContext.Provider>;
}

export function useSelection(): SelectionContextValue {
  const ctx = useContext(SelectionContext);
  if (!ctx) throw new Error('useSelection must be used inside SelectionProvider');
  return ctx;
}
