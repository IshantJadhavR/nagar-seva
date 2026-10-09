export type Role = "citizen" | "officer" | "admin";

export interface HelpRequest {
  status: "open" | "answered"; reason: string; by: string; at: string; reply: string; phone_shared: boolean;
}

export interface HistoryItem {
  old_status: string | null;
  new_status: string;
  note: string;
  created_at: string;
}

export interface Complaint {
  id: number;
  text: string;
  language: string;
  category_pred: string;
  confidence: number;
  category: string;
  secondary_category: string | null;
  department: string | null;
  priority_level: "low" | "medium" | "high" | "critical";
  priority_score: number;
  priority_breakdown: Record<string, unknown>;
  urgent: boolean;
  status: string;
  route_mode: string;
  route_reason: string;
  assigned_officer: string | null;
  lat: number | null;
  lng: number | null;
  address: string | null;
  ward: string | null;
  image_path: string | null;
  geo_address: string | null;
  geo_check: GeoCheckSaved | null;
  location_flag: "wrong" | "check_address" | "photo_far" | "help" | null;
  help_request?: HelpRequest | null;      // staff only
  citizen_phone?: string | null;          // admin always, officer only when the admin shared it
  rating: number | null;
  feedback: string | null;
  created_at: string;
  updated_at: string;
  history?: HistoryItem[];
}

export interface NearPlace { name: string | null; distance_m: number }
export interface Nearby { school: NearPlace | null; hospital: NearPlace | null; main_road: NearPlace | null }
export interface GeoCheckSaved {
  nearby?: Nearby | null; address_distance_m?: number | null; address_mismatch?: boolean;
  photo_gps?: { lat: number; lng: number }; photo_distance_m?: number;
}
export interface GeoResult {
  inside_area: boolean | null; geo_address: string | null; nearby: Nearby | null; nearby_checked: boolean;
  address_distance_m: number | null; address_mismatch: boolean; points_from_map: number; evidence: string[];
}
export interface PhotoGps { has_gps: boolean; lat?: number; lng?: number; inside_area?: boolean; address?: string | null }

export interface Prediction {
  language: string;
  category: string;
  confidence: number;
  top3: [string, number][];
  department: string | null;
  would_auto_route: boolean;
  review_reasons: string[];
  secondary_category: string | null;
  priority_level: string;
  priority_score: number;
  priority_breakdown: Record<string, unknown>;
  critical_reason: string | null;
}

export interface Analytics {
  open: number;
  resolved_total: number;
  resolution_rate: number;
  avg_resolution_hours: number | null;
  avg_rating: number | null;
  per_day: { date: string; count: number }[];
  total: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
  by_department: Record<string, number>;
  auto_routed: number;
  sent_to_review: number;
  auto_route_rate: number;
  avg_confidence: number;
  urgent_open: number;
  admin_decisions: number;
  admin_changed_prediction: number;
  hotspots: { lat: number; lng: number; count: number }[];
}
