import { post } from './client';

export interface SupersetProgrammaticRequest {
  chart_title?: string;
  dashboard_title?: string;
  viz_type?: string;
  group_by?: string;
  metric?: string;
  table_name?: string;
  schema?: string;
  create_dashboard?: boolean;
}

export interface SupersetProgrammaticResponse {
  chart_id: number;
  dashboard_id?: number | null;
  guest_token: string;
  superset_domain: string;
}

export interface SupersetDashboardEmbedRequest {
  dashboard_id: number;
}

export interface SupersetDashboardEmbedResponse {
  dashboard_id: number;
  guest_token: string;
  superset_domain: string;
}

export async function createSupersetProgrammaticChart(payload: SupersetProgrammaticRequest) {
  return post<SupersetProgrammaticResponse>('/api/superset/programmatic', payload);
}

export async function getSupersetDashboardEmbed(payload: SupersetDashboardEmbedRequest) {
  return post<SupersetDashboardEmbedResponse>('/api/superset/embed/dashboard', payload);
}
