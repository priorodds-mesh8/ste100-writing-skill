# Visual comparison

The renderer has no browser dependency. This development test uses Playwright Chromium and Pillow.

```sh
python3 -m pip install -r requirements-dev.txt
npm install
npx playwright install chromium
npm run test:visual
```

Use `STE100_TEST_PYTHON` to select another Python executable when needed. `tests/visual_compare.cjs` accepts an optional output directory. It defaults to the ignored `validation-output/` folder.

The test renders the structured historical fixture and compares it with the unchanged native export. It uses the same bundled IBM Plex font bytes for both documents. It intercepts only the reference's font stylesheet request. The reference HTML remains unchanged.

The browser loads all six font faces before screenshots. It compares panel geometry, document width, and full-page pixels at 1280, 390, 899, and 901 pixels. It runs light and dark themes. Device scale is one. Viewport height is 1000 pixels.

The new workflow fixture runs at the same widths and themes with remote requests blocked. It must have no document-wide overflow or network dependency. Screenshots, geometry, and pixel results stay in the output directory.

The build records zero changed pixels in all eight historical comparisons. This claim applies to the recorded browser, operating system, fonts, and viewports. Font rasterization can differ on another operating system. The test compares two documents in the same environment to keep that difference controlled.

Inspect the new diagram's labels and facts as well. Pixel equality for the historical fixture does not prove that every future dataset fits.
