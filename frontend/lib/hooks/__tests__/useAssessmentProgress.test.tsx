// @vitest-environment happy-dom
import { describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";
import {
  clearAssessmentProgress,
  useAssessmentProgress,
} from "../useAssessmentProgress";

describe("useAssessmentProgress", () => {
  it("starts with default state when storage is empty", () => {
    const { result } = renderHook(() => useAssessmentProgress());
    expect(result.current.progress.assessmentId).toBeNull();
    expect(result.current.progress.demographicIdx).toBe(0);
    expect(result.current.progress.mainAnswers).toEqual({});
  });

  it("persists patches to localStorage and reads them back", () => {
    const { result, unmount } = renderHook(() => useAssessmentProgress());
    act(() => {
      result.current.update({
        assessmentId: "abc-123",
        seed: "seed-xyz",
        demographicAnswers: { DEM_AGE: "20_24" },
        demographicIdx: 5,
        mainIdx: 2,
        mainAnswers: { Q1: 4, Q2: 3 },
      });
    });
    expect(result.current.progress.assessmentId).toBe("abc-123");
    expect(result.current.progress.demographicAnswers).toEqual({ DEM_AGE: "20_24" });
    expect(result.current.progress.mainAnswers).toEqual({ Q1: 4, Q2: 3 });

    unmount();

    const { result: r2 } = renderHook(() => useAssessmentProgress());
    expect(r2.current.progress.assessmentId).toBe("abc-123");
    expect(r2.current.progress.seed).toBe("seed-xyz");
    expect(r2.current.progress.mainIdx).toBe(2);
  });

  it("reset() clears state and localStorage", () => {
    const { result } = renderHook(() => useAssessmentProgress());
    act(() => {
      result.current.update({ assessmentId: "id-1", mainIdx: 4 });
    });
    expect(result.current.progress.assessmentId).toBe("id-1");
    act(() => {
      result.current.reset();
    });
    expect(result.current.progress.assessmentId).toBeNull();
    expect(result.current.progress.mainIdx).toBe(0);
    expect(localStorage.getItem("careerdna_test_progress")).toBeNull();
  });

  it("ignores corrupt localStorage data", () => {
    localStorage.setItem("careerdna_test_progress", "{not-json");
    const { result } = renderHook(() => useAssessmentProgress());
    expect(result.current.progress.assessmentId).toBeNull();
  });

  it("ignores stale (>7d) saved progress", () => {
    const stale = {
      v: 2,
      assessmentId: "old",
      seed: "",
      demographicAnswers: {},
      demographicIdx: 0,
      mainAnswers: {},
      mainIdx: 0,
      updatedAt: Date.now() - 1000 * 60 * 60 * 24 * 8,
    };
    localStorage.setItem("careerdna_test_progress", JSON.stringify(stale));
    const { result } = renderHook(() => useAssessmentProgress());
    expect(result.current.progress.assessmentId).toBeNull();
  });

  it("clearAssessmentProgress wipes the key", () => {
    localStorage.setItem("careerdna_test_progress", "anything");
    clearAssessmentProgress();
    expect(localStorage.getItem("careerdna_test_progress")).toBeNull();
  });
});
