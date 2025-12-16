import type { Metadata } from "next";
import { Providers } from "../../providers";

export const metadata: Metadata = {
  title: "Vigilancia | Epidemiología",
  description: "Sistema de Vigilancia Epidemiológica",
};

export default function VigilanciaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Providers>{children}</Providers>;
}
