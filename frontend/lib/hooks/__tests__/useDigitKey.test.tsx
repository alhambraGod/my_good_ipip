// @vitest-environment happy-dom
import { describe, expect, it, vi } from "vitest";
import { fireEvent, renderHook } from "@testing-library/react";
import { useDigitKey } from "../useDigitKey";

describe("useDigitKey", () => {
  it("calls handler with the pressed digit when within range", () => {
    const handler = vi.fn();
    renderHook(() => useDigitKey(5, handler));
    fireEvent.keyDown(window, { key: "3" });
    expect(handler).toHaveBeenCalledWith(3);
  });

  it("ignores presses above max", () => {
    const handler = vi.fn();
    renderHook(() => useDigitKey(3, handler));
    fireEvent.keyDown(window, { key: "5" });
    expect(handler).not.toHaveBeenCalled();
  });

  it("ignores presses with modifier keys", () => {
    const handler = vi.fn();
    renderHook(() => useDigitKey(5, handler));
    fireEvent.keyDown(window, { key: "1", metaKey: true });
    fireEvent.keyDown(window, { key: "1", ctrlKey: true });
    fireEvent.keyDown(window, { key: "1", altKey: true });
    expect(handler).not.toHaveBeenCalled();
  });

  it("ignores keys when an INPUT is focused", () => {
    const handler = vi.fn();
    renderHook(() => useDigitKey(5, handler));
    const input = document.createElement("input");
    document.body.appendChild(input);
    input.focus();
    fireEvent.keyDown(input, { key: "2" });
    expect(handler).not.toHaveBeenCalled();
    document.body.removeChild(input);
  });

  it("respects enabled=false", () => {
    const handler = vi.fn();
    renderHook(() => useDigitKey(5, handler, false));
    fireEvent.keyDown(window, { key: "1" });
    expect(handler).not.toHaveBeenCalled();
  });

  it("ignores non-digit keys", () => {
    const handler = vi.fn();
    renderHook(() => useDigitKey(5, handler));
    fireEvent.keyDown(window, { key: "a" });
    fireEvent.keyDown(window, { key: "Enter" });
    expect(handler).not.toHaveBeenCalled();
  });
});
