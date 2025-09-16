"use client"

import { useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { LoadingSpinner } from "@/components/ui/loading-spinner"

export default function HomePage() {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status === 'loading') return // Still loading

    if (session) {
      router.push('/dashboard')
    } else {
      router.push('/login')
    }
  }, [session, status, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="text-center">
        <LoadingSpinner className="mx-auto mb-4 h-8 w-8" />
        <p className="text-slate-600">Cargando...</p>
      </div>
    </div>
  )
}