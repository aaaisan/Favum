export interface Category {
  id: number
  name: string
  description: string
  parent_id: number | null
  order: number | null
  created_at: string
} 