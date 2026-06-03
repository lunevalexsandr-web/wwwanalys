/** Custom hook for toast notifications */
import { useState, useCallback } from 'react';
import type { ToastState } from '../types';

const initialToastState: ToastState = {
  show: false,
  message: '',
  variant: 'success'
};

export function useToast() {
  const [toast, setToast] = useState<ToastState>(initialToastState);

  const showToast = useCallback((message: string, variant: ToastState['variant'] = 'success') => {
    setToast({ show: true, message, variant });
  }, []);

  const hideToast = useCallback(() => {
    setToast(prev => ({ ...prev, show: false }));
  }, []);

  return { toast, showToast, hideToast };
}