import '@testing-library/jest-dom';

// Mock maplibre-gl to avoid DOM/WebGL requirements in tests
jest.mock('maplibre-gl', () => ({
  Map: jest.fn(() => ({
    on: jest.fn(),
    remove: jest.fn(),
    fitBounds: jest.fn(),
    addSource: jest.fn(),
    addLayer: jest.fn(),
  })),
}));

// Provide ResizeObserver mock for MUI/layout code paths
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverMock;

// Basic fetch mock used by map screen
global.fetch = jest.fn(() =>
  Promise.resolve({ json: () => Promise.resolve({ type: 'FeatureCollection', features: [] }) })
);

// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
