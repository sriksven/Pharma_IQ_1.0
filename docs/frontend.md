# Frontend

## Stack

React + Vite. Recharts for charts. React Router for navigation. CSS Modules for component styles. No UI framework.

## Design

Off-white background (`#f7f6f3`), dark text, Inter typeface. No neon colors, gradients, or gimmicks. Tables and charts are functional. The goal is something that looks like a careful engineer built it, not a product team.

## Component Structure

```
src/
  components/
    layout/     Header, Sidebar
    chat/       ChatThread, MessageBubble, SqlViewer,
                ProvenanceTag, LlmBadge, InputBar
    charts/     AutoChart (routes to BarChartView, LineChartView,
                DoughnutChartView, KpiCard, DataTable)
    common/     Spinner, ErrorBanner
  pages/
    ChatPage    Full chat interface
    MetricsPage Monitoring dashboard
  api/
    client.js   All API calls
```

## MessageBubble

Each assistant response renders:
1. Answer text
2. Collapsible SQL block
3. Auto-selected chart or data table
4. Source file tags from provenance
5. LLM badge (Groq 120B/8B, Groq 20B fallback, or Cached)

## chart_hint

The backend infers chart type from result DataFrame shape:

| Shape | Chart |
|---|---|
| Single value | KPI card |
| 1 date + 1 numeric | Line chart |
| 1 categorical + 1 numeric | Bar chart |
| Percentage column | Doughnut |
| 5+ columns | Data table |

## Routing

- `/` -- chat interface
- `/metrics` -- monitoring dashboard

## API Client

All HTTP calls are in `src/api/client.js`. Errors throw with the backend's `detail` field as the message.
