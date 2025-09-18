'use client'

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { ChartData } from '../../types'

interface ChartCardProps {
  chartData: ChartData
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0']

function LineChartComponent({ data, color }: { data: ChartData['data'], color?: string }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="value" 
          stroke={color || '#8884d8'} 
          strokeWidth={2}
          dot={{ fill: color || '#8884d8' }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

function BarChartComponent({ data, color }: { data: ChartData['data'], color?: string }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="value" fill={color || '#82ca9d'} />
      </BarChart>
    </ResponsiveContainer>
  )
}

function AreaChartComponent({ data, color }: { data: ChartData['data'], color?: string }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Area 
          type="monotone" 
          dataKey="value" 
          stroke={color || '#ffc658'} 
          fill={color || '#ffc658'} 
          fillOpacity={0.6}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

function PieChartComponent({ data }: { data: ChartData['data'] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ date, percent }) => `${date}: ${(percent * 100).toFixed(0)}%`}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((_entry: unknown, index: number) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}

export const ChartComponents = { LineChartComponent, BarChartComponent, AreaChartComponent, PieChartComponent }

export function ChartCard({ chartData }: ChartCardProps) {
  const renderChart = () => {
    switch (chartData.type) {
      case 'line':
        return <LineChartComponent data={chartData.data} color={chartData.color} />
      case 'bar':
        return <BarChartComponent data={chartData.data} color={chartData.color} />
      case 'area':
        return <AreaChartComponent data={chartData.data} color={chartData.color} />
      case 'pie':
        return <PieChartComponent data={chartData.data} />
      default:
        return <div>Tipo de gráfico no soportado</div>
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-semibold">{chartData.title}</CardTitle>
      </CardHeader>
      <CardContent>
        {renderChart()}
      </CardContent>
    </Card>
  )
}