// @vitest-environment happy-dom
import { describe, expect, it } from "vitest";
import { fmt, STRINGS } from "../strings";

describe("i18n strings", () => {
  it("has matching top-level keys for en and hi", () => {
    expect(Object.keys(STRINGS.en).sort()).toEqual(Object.keys(STRINGS.hi).sort());
  });

  it("has matching second-level keys for nav/landing/test/payment/common", () => {
    for (const ns of ["nav", "landing", "test", "payment", "common"] as const) {
      const enKeys = Object.keys(STRINGS.en[ns]).sort();
      const hiKeys = Object.keys(STRINGS.hi[ns]).sort();
      expect(hiKeys, `missing/extra keys in ${ns}`).toEqual(enKeys);
    }
  });

  it("fmt substitutes named placeholders", () => {
    expect(fmt("Hi {name}, you are {n}.", { name: "Antonio", n: 42 })).toBe(
      "Hi Antonio, you are 42.",
    );
  });

  it("fmt leaves missing variables as empty", () => {
    expect(fmt("Hello {missing}!", {})).toBe("Hello !");
  });

  it("fmt handles strings without placeholders", () => {
    expect(fmt("nothing here", { x: 1 })).toBe("nothing here");
  });
});
