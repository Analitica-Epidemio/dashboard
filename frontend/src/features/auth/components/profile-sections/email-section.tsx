"use client";

/**
 * Sección de direcciones de email
 */

interface EmailSectionProps {
  email: string;
}

export function EmailSection({ email }: EmailSectionProps) {
  return (
    <div className="flex flex-row-reverse items-start border-t pt-4 pb-4 gap-6">
      <div className="flex-shrink-0">
        <span className="text-xs px-2 py-1 bg-accent rounded">Principal</span>
      </div>
      <div className="flex flex-col gap-2 min-w-0 w-full">
        <h3 className="text-sm font-medium">Direcciones de email</h3>
        <p className="text-sm text-muted-foreground truncate">{email}</p>
        <p className="text-xs text-muted-foreground">
          El email no se puede cambiar
        </p>
      </div>
    </div>
  );
}
