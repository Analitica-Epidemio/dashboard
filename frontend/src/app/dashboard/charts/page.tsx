import { Suspense } from "react";
import { ChartsLibrary } from "@/features/charts/components/ChartsLibrary";
import { LoadingSpinner } from "@/components/ui/loading-spinner";

export default function ChartsPage() {
  return (
    <div className="container mx-auto p-6">
      <Suspense fallback={<LoadingSpinner />}>
        <ChartsLibrary />
      </Suspense>
    </div>
  );
}