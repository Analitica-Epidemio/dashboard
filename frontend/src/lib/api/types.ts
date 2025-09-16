/**
 * OpenAPI Types - Mock for Development
 * Will be auto-generated when backend is running: pnpm generate
 */

export interface paths {
  // Auth endpoints
  '/api/v1/auth/login': {
    post: {
      requestBody: {
        content: {
          'application/json': {
            email: string;
            password: string;
            remember_me?: boolean;
          };
        };
      };
      responses: {
        200: {
          content: {
            'application/json': {
              access_token: string;
              refresh_token: string;
              token_type: string;
              expires_in: number;
            };
          };
        };
      };
    };
  };

  '/api/v1/auth/refresh': {
    post: {
      requestBody: {
        content: {
          'application/json': {
            refresh_token: string;
          };
        };
      };
      responses: {
        200: {
          content: {
            'application/json': {
              access_token: string;
              refresh_token: string;
              token_type: string;
              expires_in: number;
            };
          };
        };
      };
    };
  };

  '/api/v1/auth/me': {
    get: {
      responses: {
        200: {
          content: {
            'application/json': {
              id: number;
              email: string;
              nombre: string;
              apellido: string;
              role: 'superadmin' | 'epidemiologo';
              status: 'active' | 'inactive' | 'locked';
              created_at: string;
              updated_at: string;
            };
          };
        };
      };
    };
  };

  '/api/v1/auth/logout': {
    post: {
      responses: {
        204: {
          content: never;
        };
      };
    };
  };

  // Charts endpoints
  '/api/v1/charts/dashboard': {
    get: {
      parameters: {
        query?: {
          grupo_id?: number;
          evento_id?: number;
          fecha_desde?: string;
          fecha_hasta?: string;
          clasificaciones?: string[];
        };
      };
      responses: {
        200: {
          content: {
            'application/json': {
              charts: Array<{
                codigo: string;
                nombre: string;
                descripcion: string;
                tipo: string;
                data: any;
                config: Record<string, any>;
              }>;
              total: number;
              filtros_aplicados: Record<string, any>;
            };
          };
        };
      };
    };
  };

  '/api/v1/charts/indicadores': {
    get: {
      parameters: {
        query?: {
          grupo_id?: number;
          evento_id?: number;
          fecha_desde?: string;
          fecha_hasta?: string;
          clasificaciones?: string[];
        };
      };
      responses: {
        200: {
          content: {
            'application/json': {
              total_casos: number;
              tasa_incidencia: number;
              areas_afectadas: number;
              letalidad: number;
              filtros_aplicados: Record<string, any>;
            };
          };
        };
      };
    };
  };

  '/api/v1/charts/disponibles': {
    get: {
      responses: {
        200: {
          content: {
            'application/json': Array<{
              id: number;
              codigo: string;
              nombre: string;
              descripcion: string;
              tipo_visualizacion: string;
              condiciones: any;
            }>;
          };
        };
      };
    };
  };

  // Reports endpoints
  '/api/v1/reports/generate': {
    post: {
      requestBody: {
        content: {
          'application/json': {
            date_range: {
              from: string;
              to: string;
            };
            combinations: Array<{
              id: string;
              group_id?: number;
              group_name?: string;
              event_ids: number[];
              event_names: string[];
              clasificaciones?: string[];
            }>;
            format?: string;
          };
        };
      };
      responses: {
        200: {
          content: {
            'application/pdf': Blob;
          };
        };
      };
    };
  };

  '/api/v1/reports/generate-zip': {
    post: {
      requestBody: {
        content: {
          'application/json': {
            date_range: {
              from: string;
              to: string;
            };
            combinations: Array<{
              id: string;
              group_id?: number;
              group_name?: string;
              event_ids: number[];
              event_names: string[];
              clasificaciones?: string[];
            }>;
            format?: string;
          };
        };
      };
      responses: {
        200: {
          content: {
            'application/zip': Blob;
          };
        };
      };
    };
  };

  '/api/v1/reports/preview': {
    post: {
      requestBody: {
        content: {
          'application/json': {
            date_range: {
              from: string;
              to: string;
            };
            combinations: Array<{
              id: string;
              group_id?: number;
              group_name?: string;
              event_ids: number[];
              event_names: string[];
              clasificaciones?: string[];
            }>;
          };
        };
      };
      responses: {
        200: {
          content: {
            'application/json': {
              date_range: {
                from: string;
                to: string;
              };
              combinations: Array<{
                id: string;
                group_name?: string;
                event_names: string[];
                indicadores: any;
                charts: any[];
                total_charts: number;
              }>;
              total_combinations: number;
              generated_at: string;
            };
          };
        };
      };
    };
  };

  // Uploads endpoints
  '/api/v1/uploads/csv': {
    post: {
      requestBody: {
        content: {
          'multipart/form-data': {
            file: File;
            original_filename: string;
            sheet_name: string;
          };
        };
      };
      responses: {
        202: {
          content: {
            'application/json': {
              data: {
                job_id: string;
                status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
                message: string;
                polling_url: string;
              };
            };
          };
        };
      };
    };
  };

  '/api/v1/uploads/jobs/{job_id}/status': {
    get: {
      parameters: {
        path: {
          job_id: string;
        };
      };
      responses: {
        200: {
          content: {
            'application/json': {
              data: {
                job_id: string;
                status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
                progress_percentage: number;
                current_step?: string;
                result?: any;
                error_message?: string;
                created_at: string;
                updated_at: string;
              };
            };
          };
        };
      };
    };
  };

  '/api/v1/uploads/jobs/{job_id}': {
    delete: {
      parameters: {
        path: {
          job_id: string;
        };
      };
      responses: {
        200: {
          content: {
            'application/json': {
              message: string;
            };
          };
        };
      };
    };
  };
}

export interface components {
  schemas: Record<string, any>;
}

export interface operations {
  [key: string]: any;
}