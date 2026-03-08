# PharmaIQ Frontend

This directory contains the React interface for PharmaIQ. It uses Vite as the build tool, and relies on standard CSS Modules for styling (no heavy UI frameworks like Tailwind or Bootstrap). 

## Structure
- `src/api/client.js` - Wrapper around the `fetch` API for all backend interaction.
- `src/components/chat/` - The core chat mechanics. Includes the message bubbles, SQL markdown viewer, provenance tags, and LLM badges.
- `src/components/charts/` - Auto-detecting chart components (Bar, Line, Doughnut, KPI, Data Table) using Recharts. Renders based on DuckDB output shape.
- `src/pages/` - Includes the main `ChatPage.jsx` and the `MetricsPage.jsx` telemetry dashboard.

## Aesthetics & Design Rules
The UI is designed to look like a careful, functional engineering tool. It uses an off-white background (`#f7f6f3`), dark text, and the Inter typeface. Bright neon colors and unnecessary gradients are avoided.

## Running Locally
```bash
npm install
npm run dev
```
By default, the Vite server will run on `http://localhost:5173`. Make sure the FastAPI backend is running simultaneously on port `8000`.

*For more details on the automated charting logic and frontend component hierarchy, please see the root `/docs/frontend.md` file.*
