"use client";

import React from "react";
import { CheckCircle, Upload, Eye, CheckSquare } from "lucide-react";

interface UploadStepsProps {
  currentStep: 'upload' | 'preview' | 'processing';
}

const steps = [
  {
    id: 'upload',
    title: 'Subir Archivo',
    description: 'Selecciona tu archivo Excel',
    icon: Upload,
  },
  {
    id: 'preview', 
    title: 'Revisar Datos',
    description: 'Verifica la información',
    icon: Eye,
  },
  {
    id: 'processing',
    title: 'Procesando',
    description: 'Analizando los datos',
    icon: CheckSquare,
  },
];

export function UploadSteps({ currentStep }: UploadStepsProps) {
  const getCurrentStepIndex = () => {
    return steps.findIndex(step => step.id === currentStep);
  };

  const currentStepIndex = getCurrentStepIndex();

  return (
    <div className="w-full max-w-4xl mb-6">
      <div className="flex items-center justify-center space-x-8">
        {steps.map((step, index) => {
          const isActive = index === currentStepIndex;
          const isCompleted = index < currentStepIndex;
          const IconComponent = step.icon;

          return (
            <React.Fragment key={step.id}>
              {/* Paso - diseño más compacto */}
              <div className="flex items-center space-x-2">
                {/* Ícono más pequeño */}
                <div
                  className={`
                    flex items-center justify-center w-6 h-6 rounded-full border transition-all
                    ${
                      isCompleted
                        ? 'bg-green-500 border-green-500 text-white'
                        : isActive
                        ? 'bg-primary border-primary text-primary-foreground'
                        : 'bg-muted border-border text-muted-foreground'
                    }
                  `}
                >
                  {isCompleted ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : (
                    <IconComponent className="w-4 h-4" />
                  )}
                </div>
                
                {/* Texto horizontal más sutil */}
                <div>
                  <p
                    className={`text-sm font-medium ${
                      isActive || isCompleted
                        ? 'text-foreground'
                        : 'text-muted-foreground'
                    }`}
                  >
                    {step.title}
                  </p>
                </div>
              </div>

              {/* Línea conectora más sutil */}
              {index < steps.length - 1 && (
                <div className="w-8 mx-2">
                  <div
                    className={`h-px transition-all ${
                      index < currentStepIndex
                        ? 'bg-green-500'
                        : 'bg-border'
                    }`}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}