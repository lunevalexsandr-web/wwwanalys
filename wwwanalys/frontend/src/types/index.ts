/** Common types for the application */

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface Indicator {
  id: number;
  name: string;
  unit: string;
  min_value: number | null;
  max_value: number | null;
  data_type: 'number' | 'text' | 'select';
  options?: string[];
}

export interface AnalysisType {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  indicators: Indicator[];
  created_at?: string;
}

export interface IndicatorValue {
  indicator_id: number;
  value: string | number;
  is_normal?: boolean;
}

export interface Report {
  id: number;
  batch_number: string;
  analysis_type_id: number;
  started_at: string;
  status: string;
  notes?: string;
  indicator_values?: IndicatorValueResponse[];
}

export interface IndicatorValueResponse {
  id: number;
  indicator_id: number;
  value: number | null;
  text_value: string | null;
  is_normal: boolean;
  measured_at: string;
}

export interface ToastState {
  show: boolean;
  message: string;
  variant: 'success' | 'danger' | 'warning' | 'info';
}