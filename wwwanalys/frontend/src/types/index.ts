/** Common types for the application */

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface AnalysisType {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  template_indicators?: TemplateIndicator[];
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

/** Library indicator types */
export interface IndicatorLibrary {
  id: number;
  name: string;
  unit?: string;
  data_type: 'number' | 'text' | 'select';
  options?: string[];
  description?: string | null;
  category?: string | null;
  is_required?: boolean;
  default_value?: string | null;
  validation_rules?: string | null;
  created_by?: number | null;
  created_at?: string | null;
}

export interface TemplateIndicator {
  id: number;
  indicator_id: number;
  name: string;
  unit: string;
  data_type: 'number' | 'text' | 'select';
  options?: string[];
  min_value: number | null;
  max_value: number | null;
  sort_order: number;
  is_custom?: boolean;
  template_notes?: string | null;
}

export interface LibraryIndicatorRef {
  indicator_id: number;
  min_value: number | null;
  max_value: number | null;
  sort_order: number;
  name?: string;  // имя из шаблона (фолбэк, если справочник на клиенте неполон)
  unit?: string;
}

export interface TemplateFormData {
  name: string;
  description: string;
  is_active: boolean;
  library_indicators: LibraryIndicatorRef[];
}

/** Preset types */
// Legacy indicator type (для совместимости с TemplateBuilder)
export interface Indicator {
  id: number;
  name: string;
  unit: string;
  data_type: 'number' | 'text' | 'select';
  min_value: number | null;
  max_value: number | null;
}

export interface PresetIndicator {
  id: number;
  preset_id: number;
  indicator_id: number;
  min_value: number | null;
  max_value: number | null;
  sort_order: number;
  is_required: boolean;
  indicator_name: string;
  indicator_unit: string;
  indicator_data_type: 'number' | 'text' | 'select';
  indicator_options?: string[] | null;
}

export interface Preset {
  id: number;
  name: string;
  description: string | null;
  category: string | null;
  created_at: string | null;
  created_by: number | null;
  indicators: PresetIndicator[];
}

export interface PresetListItem {
  id: number;
  name: string;
  description: string | null;
  category: string | null;
  indicators_count: number;
  created_at: string | null;
}

/** History version types */
export interface IndicatorLibraryVersion {
  id: number;
  version: number;
  indicator_id: number;
  name: string;
  unit: string;
  data_type: 'number' | 'text' | 'select';
  options?: string | null;
  description?: string | null;
  category?: string | null;
  is_required: boolean;
  default_value?: string | null;
  change_type: 'create' | 'update' | 'delete';
  change_notes?: string | null;
  changed_by?: number | null;
  created_at: string;
}

/** Planning types */
export interface PlanItem {
  id: number;
  plan_id: number;
  template_id: number;
  batch_number?: string | null;
  sort_order: number;
  is_completed: boolean;
  completed_report_id?: number | null;
  template?: PlanItemTemplateInfo;
}

export interface PlanItemTemplateInfo {
  id: number;
  name: string;
  description?: string;
  template_indicators?: TemplateIndicator[];
}

export interface AnalysisPlan {
  id: number;
  name: string;
  description?: string;
  plan_date: string;
  created_by: number;
  created_at: string;
  is_completed: boolean;
  plan_items: PlanItem[];
}

export interface PlanCreate {
  name: string;
  description?: string;
  plan_date: string;
  plan_items: { template_id: number; batch_number?: string; sort_order?: number }[];
}