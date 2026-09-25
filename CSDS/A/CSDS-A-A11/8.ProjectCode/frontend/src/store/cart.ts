import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Product } from '@/lib/types'

export type CartLine = {
  productId: string
  slug: string
  name: string
  price: number
  currency: string
  colorway?: string
  imageSeed?: string | number
  category?: string
  qty: number
  recId?: string
}

type CartState = {
  lines: CartLine[]
  isOpen: boolean
  add: (product: Product, opts?: { qty?: number; recId?: string }) => void
  remove: (productId: string) => void
  setQty: (productId: string, qty: number) => void
  clear: () => void
  setOpen: (open: boolean) => void
}

export const useCart = create<CartState>()(
  persist(
    (set) => ({
      lines: [],
      isOpen: false,
      add: (product, opts) =>
        set((state) => {
          const id = String(product.id)
          const qty = opts?.qty ?? 1
          const existing = state.lines.find((l) => l.productId === id)
          if (existing) {
            return {
              lines: state.lines.map((l) =>
                l.productId === id ? { ...l, qty: l.qty + qty, recId: l.recId ?? opts?.recId } : l,
              ),
            }
          }
          return {
            lines: [
              ...state.lines,
              {
                productId: id,
                slug: product.slug,
                name: product.name,
                price: product.price,
                currency: product.currency ?? 'USD',
                colorway: product.colorway,
                imageSeed: product.image_seed ?? product.slug,
                category: product.category,
                qty,
                recId: opts?.recId,
              },
            ],
          }
        }),
      remove: (productId) =>
        set((state) => ({ lines: state.lines.filter((l) => l.productId !== productId) })),
      setQty: (productId, qty) =>
        set((state) => ({
          lines:
            qty <= 0
              ? state.lines.filter((l) => l.productId !== productId)
              : state.lines.map((l) => (l.productId === productId ? { ...l, qty } : l)),
        })),
      clear: () => set({ lines: [] }),
      setOpen: (isOpen) => set({ isOpen }),
    }),
    { name: 'nuvara.cart', version: 1, partialize: (s) => ({ lines: s.lines }) },
  ),
)

export const cartCount = (lines: CartLine[]) => lines.reduce((sum, l) => sum + l.qty, 0)
export const cartSubtotal = (lines: CartLine[]) =>
  lines.reduce((sum, l) => sum + l.qty * l.price, 0)
