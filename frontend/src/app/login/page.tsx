"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { SecretariaDeSaludLogo } from "@/components/assets/logo-secretaria-de-salud";

// Validation schema
const loginSchema = z.object({
  email: z
    .string()
    .min(1, "El email es obligatorio")
    .email("Formato de email inválido"),
  password: z.string().min(1, "La contraseña es obligatoria"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  // TODO: Implement proper login with NextAuth
  const login = (data: LoginFormData) => console.log('Login:', data);
  const isLoggingIn = false;
  const loginError: string | null = null;

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: "onChange",
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = form;

  const onSubmit = handleSubmit((data) => {
    login(data);
  });

  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-muted p-6 md:p-10">
      <div className="min-w-[450px] max-w-sm md:max-w-4xl">
        <Card className="overflow-hidden border p-0 shadow-none">
          <div className="grid md:grid-cols-1 gap-0 min-h-[600px]">
            {/* Formulario de Login */}
            <div className="p-4 md:p-4 flex flex-col justify-center bg-card">
              <div className="flex flex-col gap-8 max-w-sm mx-auto w-full">
                <div className="flex flex-col items-center text-center gap-6">
                  <SecretariaDeSaludLogo className="w-full max-w-[240px] h-auto" />
                  <div className="space-y-2">
                    <h1 className="text-2xl font-semibold text-foreground">
                      Sistema de Epidemiología
                    </h1>
                    <p className="text-sm text-muted-foreground">
                      Ingresa tus credenciales para acceder
                    </p>
                  </div>
                </div>

                <form onSubmit={onSubmit} className="grid gap-5">
                  {loginError && (
                    <Alert variant="destructive">
                      <AlertDescription>{loginError}</AlertDescription>
                    </Alert>
                  )}

                  <div className="grid gap-2">
                    <Label htmlFor="email" className="text-sm font-medium">
                      Email
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="tu@email.com"
                      {...register("email")}
                      disabled={isLoggingIn}
                      aria-invalid={errors.email ? "true" : "false"}
                    />
                    {errors.email && (
                      <p className="text-sm text-destructive" role="alert">
                        {errors.email.message}
                      </p>
                    )}
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="password" className="text-sm font-medium">
                      Contraseña
                    </Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="••••••••"
                      {...register("password")}
                      disabled={isLoggingIn}
                      aria-invalid={errors.password ? "true" : "false"}
                    />
                    {errors.password && (
                      <p className="text-sm text-destructive" role="alert">
                        {errors.password.message}
                      </p>
                    )}
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={isLoggingIn || !isValid}
                  >
                    {isLoggingIn ? (
                      <>
                        <LoadingSpinner className="mr-2 h-4 w-4" />
                        Iniciando sesión...
                      </>
                    ) : (
                      "Iniciar Sesión"
                    )}
                  </Button>
                </form>

                <div className="text-center text-xs text-muted-foreground">
                  ¿Problemas para acceder?{" "}
                  <button className="underline underline-offset-4 hover:text-foreground transition-colors">
                    Contacta al administrador
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
