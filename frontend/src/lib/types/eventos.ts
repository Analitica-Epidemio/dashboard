/**
 * Tipos compartidos para eventos y grupos
 * Usados por dashboard, eventos, reports, etc.
 */

export interface Event {
  id: string
  name: string
  groupId?: string | null
  description?: string | null | undefined
  groupName?: string | null | undefined
}

export interface Group {
  id: string
  name: string
  description?: string | null
  eventos?: Event[] // Eventos incluidos en este grupo (del backend)
}
