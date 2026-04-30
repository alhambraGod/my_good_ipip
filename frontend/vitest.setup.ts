import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Node 25 ships a partial built-in localStorage that masks/breaks the one
// shipped by happy-dom. Replace both with a clean in-memory Storage so
// hooks like useSyncExternalStore that bind to localStorage work.
class MemoryStorage implements Storage {
  private map = new Map<string, string>();
  get length(): number {
    return this.map.size;
  }
  clear(): void {
    this.map.clear();
  }
  key(i: number): string | null {
    return Array.from(this.map.keys())[i] ?? null;
  }
  getItem(k: string): string | null {
    return this.map.has(k) ? (this.map.get(k) as string) : null;
  }
  setItem(k: string, v: string): void {
    this.map.set(k, String(v));
  }
  removeItem(k: string): void {
    this.map.delete(k);
  }
  [name: string]: unknown;
}

const lsImpl = new MemoryStorage();
const ssImpl = new MemoryStorage();

if (typeof globalThis !== "undefined") {
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    writable: true,
    value: lsImpl,
  });
  Object.defineProperty(globalThis, "sessionStorage", {
    configurable: true,
    writable: true,
    value: ssImpl,
  });
}
if (typeof window !== "undefined") {
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    writable: true,
    value: lsImpl,
  });
  Object.defineProperty(window, "sessionStorage", {
    configurable: true,
    writable: true,
    value: ssImpl,
  });
}

beforeEach(() => {
  lsImpl.clear();
  ssImpl.clear();
});
afterEach(() => {
  cleanup();
  lsImpl.clear();
  ssImpl.clear();
});
