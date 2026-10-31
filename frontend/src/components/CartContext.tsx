'use client';

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';

type CartContextValue = {
  count: number;
  addToCart: () => void;
};

const CartContext = createContext<CartContextValue>({ count: 0, addToCart: () => {} });

export function CartProvider({ children }: { children: ReactNode }) {
  const [count, setCount] = useState(0);
  const addToCart = useCallback(() => setCount((c) => c + 1), []);
  const value = useMemo(() => ({ count, addToCart }), [count, addToCart]);
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  return useContext(CartContext);
}
