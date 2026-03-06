import {
    BarChart as ReBar,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    LineChart as ReLine,
    Line,
    PieChart,
    Pie,
    Cell,
    Legend,
} from 'recharts'
import styles from './AutoChart.module.css'

const COLORS = ['#2d5986', '#4a7fb5', '#7aafd4', '#a8cde8', '#c9e0f0']

export function BarChartView({ data, xKey, yKey }) {
    return (
        <ResponsiveContainer width="100%" height={220}>
            <ReBar data={data} margin={{ top: 4, right: 12, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0dbd3" />
                <XAxis dataKey={xKey} tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey={yKey} fill="#2d5986" radius={[2, 2, 0, 0]} />
            </ReBar>
        </ResponsiveContainer>
    )
}

export function LineChartView({ data, xKey, yKey }) {
    return (
        <ResponsiveContainer width="100%" height={220}>
            <ReLine data={data} margin={{ top: 4, right: 12, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0dbd3" />
                <XAxis dataKey={xKey} tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line
                    type="monotone"
                    dataKey={yKey}
                    stroke="#2d5986"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                />
            </ReLine>
        </ResponsiveContainer>
    )
}

export function DoughnutChartView({ data, xKey, yKey }) {
    return (
        <ResponsiveContainer width="100%" height={220}>
            <PieChart>
                <Pie
                    data={data}
                    dataKey={yKey}
                    nameKey={xKey}
                    cx="50%"
                    cy="50%"
                    innerRadius={56}
                    outerRadius={88}
                >
                    {data.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                </Pie>
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
        </ResponsiveContainer>
    )
}

export function KpiCard({ data, yKey }) {
    const value = data[0]?.[yKey]
    return (
        <div className={styles.kpi}>
            <div className={styles.kpiValue}>{value?.toLocaleString() ?? '--'}</div>
            <div className={styles.kpiLabel}>{yKey}</div>
        </div>
    )
}

export function DataTable({ data }) {
    if (!data || data.length === 0) return null
    const cols = Object.keys(data[0])
    return (
        <div className={styles.tableWrapper}>
            <table className={styles.table}>
                <thead>
                    <tr>
                        {cols.map((c) => <th key={c}>{c}</th>)}
                    </tr>
                </thead>
                <tbody>
                    {data.slice(0, 20).map((row, i) => (
                        <tr key={i}>
                            {cols.map((c) => <td key={c}>{row[c]}</td>)}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export default function AutoChart({ chartHint, data }) {
    if (!chartHint || !data || data.length === 0) return null

    const { type, x_column: xKey, y_column: yKey } = chartHint

    if (type === 'kpi') return <KpiCard data={data} yKey={yKey} />
    if (type === 'bar') return <BarChartView data={data} xKey={xKey} yKey={yKey} />
    if (type === 'line') return <LineChartView data={data} xKey={xKey} yKey={yKey} />
    if (type === 'doughnut') return <DoughnutChartView data={data} xKey={xKey} yKey={yKey} />
    return <DataTable data={data} />
}
