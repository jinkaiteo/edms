import { useState, useEffect } from 'react';

interface DashboardStats {
  totalDocuments: number;
  pendingReviews: number;
  pendingApprovals: number;
  effectiveDocuments: number;
}

/**
 * Simplified dashboard updates using HTTP polling
 * No WebSocket dependency - simple and reliable
 */
export const useDashboardUpdates = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalDocuments: 0,
    pendingReviews: 0,
    pendingApprovals: 0,
    effectiveDocuments: 0
  });
  const [loading, setLoading] = useState(false);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch('/api/v1/dashboard/stats/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  // Poll for updates every 60 seconds
  useEffect(() => {
    fetchDashboardStats();
    const interval = setInterval(fetchDashboardStats, 60000);
    return () => clearInterval(interval);
  }, []);

  return {
    stats,
    loading,
    refreshStats: fetchDashboardStats
  };
};
