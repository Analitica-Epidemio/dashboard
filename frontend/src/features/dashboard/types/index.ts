// Dashboard types
export interface Group {
  id: string
  name: string
  description?: string | null
}

export interface Event {
  id: string
  name: string
  groupId: string
  description?: string | null | undefined
  groupName?: string | null | undefined
}

export interface ChartDataPoint {
  date: string
  value: number
  category?: string
}

export interface DashboardFilters {
  selectedGroupId: string | null
  selectedEventId: string | null
}

export interface ChartData {
  title: string
  data: ChartDataPoint[]
  type: 'line' | 'bar' | 'area' | 'pie'
  color?: string
}