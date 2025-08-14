export interface ApiError {
  error: boolean;
  message: string;
  status_code: number;
  path: string;
  details?: unknown[];
}