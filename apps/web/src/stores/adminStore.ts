import { create } from 'zustand';

export interface DashboardMetrics {
  users: {
    total: number;
    pending: number;
    approved: number;
  };
  documents: {
    total: number;
    processing: number;
    completed: number;
    failed: number;
  };
  system: {
    uptime: string;
    version: string;
    lastBackup: string;
  };
}

interface AdminState {
  dashboardMetrics: DashboardMetrics | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  fetchMetrics: () => Promise<void>;
  refreshMetrics: () => Promise<void>;
  clearError: () => void;
}

const useAdminStore = create<AdminState>((set, get) => ({
  dashboardMetrics: null,
  isLoading: false,
  error: null,
  lastUpdated: null,

  fetchMetrics: async () => {
    const { isLoading } = get();
    if (isLoading) return;

    set({ isLoading: true, error: null });

    try {
      // Use the working test endpoint for now and correct token name
      const response = await fetch('http://localhost:8001/api/admin/dashboard/test', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Access denied. Admin privileges required.');
        }
        if (response.status === 401) {
          throw new Error('Authentication required. Please log in.');
        }
        throw new Error(`Failed to fetch metrics: ${response.statusText}`);
      }

      const metrics: DashboardMetrics = await response.json();
      
      set({ 
        dashboardMetrics: metrics, 
        isLoading: false, 
        error: null,
        lastUpdated: new Date() 
      });
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to fetch metrics' 
      });
    }
  },

  refreshMetrics: async () => {
    await get().fetchMetrics();
  },

  clearError: () => {
    set({ error: null });
  },
}));

export default useAdminStore;