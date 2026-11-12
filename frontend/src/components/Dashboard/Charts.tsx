import React from 'react'
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts'
import {
  PieChart as PieIcon,
  TrendingUp,
  BarChart3,
  Gauge,
} from 'lucide-react'
import Card from '@/components/common/Card'

interface DocumentTypeSlice {
  name: string
  value: number
  color: string
}

interface DailyQueryPoint {
  date: string
  queries: number
  hybridRate?: number
}

interface ConfidenceBucket {
  range: string
  label?: string
  count: number
  tier: string
}

interface LatencyStagePoint {
  stage: string
  latency: number
  target?: number
  color?: string
}

interface ChartsProps {
  documentTypes?: DocumentTypeSlice[]
  dailyQueries?: DailyQueryPoint[]
  confidenceDist?: ConfidenceBucket[]
  latencyBreakdown?: LatencyStagePoint[]
}

// Custom Glassmorphism Tooltip for Recharts
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border border-white/10 bg-jet-900/95 p-3 shadow-glass-lg backdrop-blur-md">
        {label && <p className="mb-1 text-xs font-semibold text-jet-200">{label}</p>}
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center space-x-2 text-xs">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: entry.color || entry.fill || '#007BA7' }}
            />
            <span className="text-jet-400 capitalize">{entry.name}:</span>
            <span className="font-mono font-bold text-white">
              {entry.value.toLocaleString()}
              {entry.unit || ''}
            </span>
          </div>
        ))}
      </div>
    )
  }
  return null
}

export const Charts: React.FC<ChartsProps> = ({
  documentTypes = [
    { name: 'PDF', value: 14, color: '#007BA7' },
    { name: 'DOCX', value: 5, color: '#189FD2' },
    { name: 'TXT', value: 3, color: '#FF2D95' },
    { name: 'Markdown', value: 2, color: '#A4A4B8' },
  ],
  dailyQueries = [
    { date: 'Oct 22', queries: 284 },
    { date: 'Oct 23', queries: 342 },
    { date: 'Oct 24', queries: 415 },
    { date: 'Oct 25', queries: 389 },
    { date: 'Oct 26', queries: 512 },
    { date: 'Oct 27', queries: 640 },
    { date: 'Oct 28', queries: 588 },
  ],
  confidenceDist = [
    { range: '90-100%', count: 482, tier: 'High Tier' },
    { range: '80-89%', count: 184, tier: 'Good Tier' },
    { range: '70-79%', count: 68, tier: 'Moderate' },
    { range: '<70%', count: 24, tier: 'Low' },
  ],
  latencyBreakdown = [
    { stage: 'Hybrid Retrieval', latency: 124, color: '#007BA7' },
    { stage: 'Cross-Encoder', latency: 78, color: '#FF2D95' },
    { stage: 'LLM Generation', latency: 266, color: '#189FD2' },
    { stage: 'Overhead', latency: 22, color: '#78788C' },
  ],
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 1. Document Types (Pie / Donut Chart) */}
      <Card variant="cerulean" className="p-6 flex flex-col justify-between">
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-cerulean/10 border border-cerulean/30 flex items-center justify-center text-cerulean-light">
              <PieIcon className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-jet-100">Document Types Distribution</h3>
              <p className="text-xs text-jet-400 mt-0.5">Corpus breakdown by mime format</p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-jet-900 text-jet-300 border border-white/5">
            Pie Chart
          </span>
        </div>

        <div className="h-64 w-full mt-4 flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Tooltip content={<CustomTooltip />} />
              <Pie
                data={documentTypes}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={4}
              >
                {documentTypes.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.color}
                    stroke="rgba(10, 10, 10, 0.8)"
                    strokeWidth={2}
                  />
                ))}
              </Pie>
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(val) => (
                  <span className="text-xs text-jet-300 font-medium px-1">{val}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* 2. Daily Queries (Line Chart) */}
      <Card variant="cerulean" className="p-6 flex flex-col justify-between">
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-cerulean/10 border border-cerulean/30 flex items-center justify-center text-cerulean-light">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-jet-100">Daily Query Volume</h3>
              <p className="text-xs text-jet-400 mt-0.5">7-day throughput & inquiry trend</p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-jet-900 text-jet-300 border border-white/5">
            Line Chart
          </span>
        </div>

        <div className="h-64 w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={dailyQueries} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
              <XAxis
                dataKey="date"
                stroke="#78788C"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#78788C"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="queries"
                name="Queries"
                stroke="#007BA7"
                strokeWidth={3}
                dot={{ fill: '#007BA7', stroke: '#189FD2', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, fill: '#189FD2', stroke: '#FFFFFF', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* 3. Confidence Distribution (Bar Chart) */}
      <Card variant="cerulean" className="p-6 flex flex-col justify-between">
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-cerulean/10 border border-cerulean/30 flex items-center justify-center text-cerulean-light">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-jet-100">Confidence Distribution</h3>
              <p className="text-xs text-jet-400 mt-0.5">Frequency across calibrated confidence tiers</p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-jet-900 text-jet-300 border border-white/5">
            Bar Chart
          </span>
        </div>

        <div className="h-64 w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={confidenceDist} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
              <XAxis
                dataKey="range"
                stroke="#78788C"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#78788C"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="count"
                name="Inquiries"
                fill="#007BA7"
                radius={[6, 6, 0, 0]}
              >
                {confidenceDist.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index === 0 ? '#007BA7' : index === 1 ? '#189FD2' : index === 2 ? '#FF2D95' : '#78788C'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* 4. Latency Breakdown (Horizontal Bar Chart) */}
      <Card variant="cerulean" className="p-6 flex flex-col justify-between">
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-cerulean/10 border border-cerulean/30 flex items-center justify-center text-cerulean-light">
              <Gauge className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-jet-100">Latency Breakdown</h3>
              <p className="text-xs text-jet-400 mt-0.5">Execution time by sub-pipeline phase</p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-jet-900 text-jet-300 border border-white/5">
            Horizontal Bar
          </span>
        </div>

        <div className="h-64 w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              layout="vertical"
              data={latencyBreakdown}
              margin={{ top: 10, right: 30, left: 35, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" horizontal={false} />
              <XAxis
                type="number"
                stroke="#78788C"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                unit="ms"
              />
              <YAxis
                dataKey="stage"
                type="category"
                stroke="#78788C"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="latency"
                name="Duration (ms)"
                radius={[0, 6, 6, 0]}
              >
                {latencyBreakdown.map((entry, index) => (
                  <Cell
                    key={`bar-cell-${index}`}
                    fill={entry.color || '#007BA7'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}

export default Charts

