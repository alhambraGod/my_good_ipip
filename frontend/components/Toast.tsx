"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { AnimatePresence, motion } from "framer-motion";

type ToastVariant = "info" | "success" | "error";
type Toast = {
  id: number;
  text: string;
  variant: ToastVariant;
  ttlMs: number;
};

type ToastContextValue = {
  push: (text: string, variant?: ToastVariant, ttlMs?: number) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idRef = useRef(0);

  const push = useCallback<ToastContextValue["push"]>(
    (text, variant = "info", ttlMs = 4000) => {
      idRef.current += 1;
      const id = idRef.current;
      setToasts((curr) => [...curr, { id, text, variant, ttlMs }]);
    },
    [],
  );

  const remove = useCallback((id: number) => {
    setToasts((curr) => curr.filter((t) => t.id !== id));
  }, []);

  const value = useMemo(() => ({ push }), [push]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 max-w-md w-[calc(100%-2rem)] pointer-events-none">
        <AnimatePresence>
          {toasts.map((t) => (
            <ToastBubble key={t.id} toast={t} onDone={() => remove(t.id)} />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

function ToastBubble({ toast, onDone }: { toast: Toast; onDone: () => void }) {
  useEffect(() => {
    const handle = setTimeout(onDone, toast.ttlMs);
    return () => clearTimeout(handle);
  }, [toast.ttlMs, onDone]);

  const variantClass: Record<ToastVariant, string> = {
    info: "bg-white text-navy-text border-saffron-700/20",
    success: "bg-india-green-600 text-white border-india-green-700",
    error: "bg-red-600 text-white border-red-700",
  };

  return (
    <motion.div
      role="status"
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className={`pointer-events-auto rounded-2xl px-4 py-3 shadow-lg border text-sm font-medium ${variantClass[toast.variant]}`}
    >
      {toast.text}
    </motion.div>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    return {
      push: (text) => {
        if (typeof window !== "undefined") {
          console.warn("Toast outside provider:", text);
        }
      },
    };
  }
  return ctx;
}
