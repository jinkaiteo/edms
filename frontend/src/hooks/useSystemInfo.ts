import { useState, useEffect } from 'react';
import apiService from '../services/api.ts';

interface SystemInfo {
  application: {
    version: string;
    build_date: string;
    environment: string;
  };
  backend: {
    framework: string;
    version: string;
    python_version: string;
  };
  database: {
    type: string;
    version: string;
    status: string;
  };
  server: {
    platform: string;
  };
  timestamp: string;
}

export const useSystemInfo = () => {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSystemInfo = async () => {
      try {
        setLoading(true);
        const data = await apiService.get('/system/info/');
        setSystemInfo(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch system info:', err);
        setError('Failed to load system information');
        // Fallback to hardcoded values
        setSystemInfo({
          application: {
            version: process.env.REACT_APP_VERSION || '1.3.3',
            build_date: process.env.REACT_APP_BUILD_DATE || '2026-02-08',
            environment: process.env.NODE_ENV || 'development',
          },
          backend: {
            framework: 'Django',
            version: 'Unknown',
            python_version: 'Unknown',
          },
          database: {
            type: 'PostgreSQL',
            version: 'Unknown',
            status: 'Unknown',
          },
          server: {
            platform: 'Unknown',
          },
          timestamp: new Date().toISOString(),
        });
      } finally {
        setLoading(false);
      }
    };

    fetchSystemInfo();
  }, []);

  return { systemInfo, loading, error };
};
