// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TableOfContents, type TocItem } from "@/components/TableOfContents";

const ITEMS: TocItem[] = [
  { id: "overview", label: "Overview", emoji: "🎯" },
  { id: "deep-dive", label: "Deep dive", emoji: "🧠" },
  { id: "careers", label: "Careers (5)", emoji: "💼" },
];

function setupSections(ids: string[]) {
  ids.forEach((id) => {
    const el = document.createElement("section");
    el.id = id;
    el.style.height = "1000px";
    document.body.appendChild(el);
  });
}

class StubObserver {
  callback: IntersectionObserverCallback;
  observed: Element[] = [];
  constructor(cb: IntersectionObserverCallback) {
    this.callback = cb;
  }
  observe(t: Element) {
    this.observed.push(t);
  }
  unobserve() {}
  disconnect() {}
  takeRecords() {
    return [];
  }
  trigger(visibleIds: string[]) {
    const entries = this.observed.map((target) => ({
      target,
      isIntersecting: visibleIds.includes(target.id),
      intersectionRatio: visibleIds.includes(target.id) ? 1 : 0,
      boundingClientRect: target.getBoundingClientRect(),
      intersectionRect: target.getBoundingClientRect(),
      rootBounds: null,
      time: Date.now(),
    })) as unknown as IntersectionObserverEntry[];
    this.callback(entries, this as unknown as IntersectionObserver);
  }
}

let lastObserver: StubObserver | null = null;

beforeEach(() => {
  lastObserver = null;
  // Stub global IntersectionObserver with a real class that captures each
  // instance via the static helper so tests can fire entries manually.
  class TestIntersectionObserver extends StubObserver {
    static last: StubObserver | null = null;
    constructor(cb: IntersectionObserverCallback) {
      super(cb);
      TestIntersectionObserver.last = this;
      lastObserver = TestIntersectionObserver.last;
    }
  }
  vi.stubGlobal("IntersectionObserver", TestIntersectionObserver);
});

afterEach(() => {
  vi.unstubAllGlobals();
  document.body.innerHTML = "";
});

describe("<TableOfContents />", () => {
  it("renders one desktop link + one mobile chip per item", () => {
    setupSections(ITEMS.map((i) => i.id));
    render(<TableOfContents items={ITEMS} />);
    // Desktop nav has aria-label
    const nav = screen.getByRole("navigation", { name: "Report sections" });
    expect(nav.querySelectorAll("a")).toHaveLength(ITEMS.length);
    // Mobile chips: total `<a>` in document = 2× items (desktop + mobile)
    expect(document.querySelectorAll("a")).toHaveLength(ITEMS.length * 2);
  });

  it("first item is initially active in the desktop nav", () => {
    setupSections(ITEMS.map((i) => i.id));
    render(<TableOfContents items={ITEMS} />);
    const navLink = screen.getByRole("navigation", { name: "Report sections" })
      .querySelector(`a[href="#${ITEMS[0].id}"]`);
    expect(navLink?.className).toMatch(/border-saffron-500/);
  });

  it("updates active item when IntersectionObserver fires", () => {
    setupSections(ITEMS.map((i) => i.id));
    render(<TableOfContents items={ITEMS} />);
    expect(lastObserver).not.toBeNull();
    act(() => {
      lastObserver!.trigger([ITEMS[1].id]);
    });
    const nav = screen.getByRole("navigation", { name: "Report sections" });
    const second = nav.querySelector(`a[href="#${ITEMS[1].id}"]`);
    expect(second?.className).toMatch(/border-saffron-500/);
    const first = nav.querySelector(`a[href="#${ITEMS[0].id}"]`);
    expect(first?.className).not.toMatch(/border-saffron-500/);
  });

  it("clicking an anchor calls scrollIntoView and updates the URL hash", async () => {
    setupSections(ITEMS.map((i) => i.id));
    const scrollSpy = vi.fn();
    Element.prototype.scrollIntoView = scrollSpy;
    const user = userEvent.setup();
    render(<TableOfContents items={ITEMS} />);
    const nav = screen.getByRole("navigation", { name: "Report sections" });
    const careersLink = nav.querySelector<HTMLAnchorElement>(
      `a[href="#${ITEMS[2].id}"]`,
    )!;
    await user.click(careersLink);
    expect(scrollSpy).toHaveBeenCalled();
    expect(window.location.hash).toBe(`#${ITEMS[2].id}`);
  });

  it("renders without IntersectionObserver in environments that lack it", () => {
    vi.unstubAllGlobals();
    delete (window as unknown as { IntersectionObserver?: unknown })
      .IntersectionObserver;
    setupSections(ITEMS.map((i) => i.id));
    render(<TableOfContents items={ITEMS} />);
    // First item still highlighted by default state, no crash
    const nav = screen.getByRole("navigation", { name: "Report sections" });
    expect(nav.querySelectorAll("a")).toHaveLength(ITEMS.length);
  });
});
