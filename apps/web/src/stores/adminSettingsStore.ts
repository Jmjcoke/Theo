import { create } from 'zustand';

export interface SystemConfiguration {
  upload: {
    max_file_size_biblical: number;
    max_file_size_theological: number;
    allowed_extensions: string[];
    max_daily_uploads: number;
  };
  system: {
    maintenance_mode: boolean;
    backup_enabled: boolean;
    backup_frequency: string;
    system_version: string;
  };
  processing: {
    max_concurrent_jobs: number;
    job_timeout_minutes: number;
    retry_attempts: number;
  };
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime: string;
  version: string;
  database: {
    status: 'connected' | 'disconnected' | 'error';
    response_time: number;
  };
  redis: {
    status: 'connected' | 'disconnected' | 'error';
    response_time: number;
  };
  storage: {
    status: 'available' | 'unavailable' | 'error';
    free_space: string;
  };
  last_updated: string;
}

interface AdminSettingsState {
  configurations: SystemConfiguration | null;
  systemHealth: SystemHealth | null;
  isLoading: boolean;
  error: string | null;
  fetchSettings: () => Promise<void>;
  updateSetting: (category: string, key: string, value: any) => Promise<void>;
  fetchSystemHealth: () => Promise<void>;
  clearError: () => void;
}

const useAdminSettingsStore = create<AdminSettingsState>((set, get) => ({
  configurations: null,
  systemHealth: null,
  isLoading: false,
  error: null,

  fetchSettings: async () => {
    const { isLoading } = get();
    if (isLoading) return;

    set({ isLoading: true, error: null });

    try {
      const response = await fetch('http://localhost:8001/api/admin/settings/test', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Unauthorized access. Please log in again.');
        }
        if (response.status === 403) {
          throw new Error('Access forbidden. Admin privileges required.');
        }
        throw new Error(`Failed to fetch settings: ${response.statusText}`);
      }

      const data = await response.json();
      set({ 
        configurations: data.configurations,
        isLoading: false,
        error: null
      });
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to fetch system settings'
      });
    }
  },

  updateSetting: async (category: string, key: string, value: any) => {
    const { configurations } = get();
    if (!configurations) return;

    set({ isLoading: true, error: null });

    try {
      const response = await fetch('http://localhost:8001/api/admin/settings', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category,
          key,
          value,
          change_reason: `Updated ${key} in ${category} configuration`
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Unauthorized access. Please log in again.');
        }
        if (response.status === 403) {
          throw new Error('Access forbidden. Admin privileges required.');
        }
        throw new Error(`Failed to update setting: ${response.statusText}`);
      }

      // Update local state optimistically
      const updatedConfigurations = {
        ...configurations,
        [category]: {
          ...configurations[category as keyof SystemConfiguration],
          [key]: value
        }
      };

      set({ 
        configurations: updatedConfigurations,
        isLoading: false,
        error: null
      });
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to update setting'
      });
      throw error; // Re-throw to handle in component
    }
  },

  fetchSystemHealth: async () => {
    try {
      const response = await fetch('http://localhost:8001/api/admin/system/health', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // Health check failed but don't throw error - this is non-critical
        return;
      }

      const data = await response.json();
      set({ systemHealth: data });
    } catch (error) {
      // Health check failed but don't set error state - this is non-critical
      // Could optionally log to a proper logging service here
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));

export default useAdminSettingsStore;