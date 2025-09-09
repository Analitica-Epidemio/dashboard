/**
 * Toggle para mostrar/ocultar sidebar en mobile
 * Mejora la experiencia en pantallas pequeñas
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import { Menu, X } from 'lucide-react';

interface MobileToggleProps {
  isOpen: boolean;
  onToggle: () => void;
}

export const MobileToggle: React.FC<MobileToggleProps> = ({ isOpen, onToggle }) => {
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onToggle}
      className="lg:hidden fixed top-4 left-4 z-50 bg-white border border-gray-200 shadow-sm"
    >
      {isOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
    </Button>
  );
};