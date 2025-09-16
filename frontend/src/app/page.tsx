"use client"

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { z } from 'zod'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Checkbox } from "@/components/ui/checkbox"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

// Validation schema
const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'El email es obligatorio')
    .email('Formato de email inválido'),
  password: z
    .string()
    .min(1, 'La contraseña es obligatoria')
    .min(8, 'La contraseña debe tener al menos 8 caracteres'),
  remember_me: z.boolean(),
})

type LoginFormData = z.infer<typeof loginSchema>

// Login API function
const loginUser = async (data: LoginFormData) => {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_HOST}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || 'Error al iniciar sesión')
  }

  return response.json()
}

export default function LoginPage() {
  const router = useRouter()

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onChange',
    defaultValues: {
      email: '',
      password: '',
      remember_me: false,
    },
  })

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid },
  } = form

  const rememberMe = watch('remember_me')

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (data) => {
      // Guardar tokens en localStorage
      localStorage.setItem('access_token', data.access_token)
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token)
      }

      // Redirigir al dashboard
      router.push('/dashboard')
    },
  })

  const onSubmit = handleSubmit((data) => {
    loginMutation.mutate(data)
  })

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-2xl font-bold text-slate-900">
            Sistema de Epidemiología
          </CardTitle>
          <CardDescription className="text-slate-600">
            Ingresa tus credenciales para acceder al sistema
          </CardDescription>
        </CardHeader>

        <form onSubmit={onSubmit}>
          <CardContent className="space-y-4">
            {loginMutation.error && (
              <Alert variant="destructive">
                <AlertDescription>
                  {loginMutation.error.message}
                </AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-700">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="tu.email@ejemplo.com"
                {...register('email')}
                disabled={loginMutation.isPending}
                className="transition-colors"
                aria-invalid={errors.email ? 'true' : 'false'}
              />
              {errors.email && (
                <p className="text-sm text-red-600" role="alert">
                  {errors.email.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-700">
                Contraseña
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                {...register('password')}
                disabled={loginMutation.isPending}
                className="transition-colors"
                aria-invalid={errors.password ? 'true' : 'false'}
              />
              {errors.password && (
                <p className="text-sm text-red-600" role="alert">
                  {errors.password.message}
                </p>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(checked) => setValue('remember_me', checked as boolean)}
                disabled={loginMutation.isPending}
              />
              <Label htmlFor="remember" className="text-sm text-slate-600">
                Mantener sesión iniciada
              </Label>
            </div>
          </CardContent>

          <CardFooter>
            <Button
              type="submit"
              className="w-full transition-all duration-200"
              disabled={loginMutation.isPending || !isValid}
            >
              {loginMutation.isPending ? (
                <>
                  <LoadingSpinner className="mr-2 h-4 w-4" />
                  Iniciando sesión...
                </>
              ) : (
                'Iniciar Sesión'
              )}
            </Button>
          </CardFooter>
        </form>

        <div className="px-6 pb-6">
          <div className="text-center text-sm text-slate-500">
            <p>¿Problemas para acceder?</p>
            <p className="text-xs mt-1">
              Contacta al administrador del sistema
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}