import "@testing-library/jest-dom/vitest";

// axe probes canvas for icon ligatures; jsdom has no native canvas context.
HTMLCanvasElement.prototype.getContext = (() => null) as typeof HTMLCanvasElement.prototype.getContext;
