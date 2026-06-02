// ========================================
// 类型定义：前后端接口约定
// 与 A/B 成员约定的 JSON 字段保持一致
// ========================================

// 量表分数
export interface ScaleScores {
  MMSE: number;
  MOCA: number;
  CDR_global: number;
  CDR_SB: number;
  HIS: number;
}

// VR 行为摘要
export interface VRSummary {
  grid4_success_rate: number;
  grid9_success_rate: number;
  grid4_wrong_pickup_rate: number;
  grid9_wrong_pickup_rate: number;
  grid4_map_ratio: number;
  grid9_map_ratio: number;
  grid4_speed_mean: number;
  grid9_speed_mean: number;
  grid4_path_distance: number;
  grid9_path_distance: number;
  grid4_stop_ratio: number;
  grid9_stop_ratio: number;
  grid4_success_time_mean: number;
  grid9_success_time_mean: number;
  grid4_duration: number;
  grid9_duration: number;
}

// 风险评估
export interface RiskAssessment {
  probability: number;
  score: number;
  level: string;
}

// 数据概览
export interface DataSummary {
  subject_count: number;
  matched_count: number;
  grid4_log_count: number;
  grid9_log_count: number;
  excluded_log_count: number;
}

// 被试列表项
export interface SubjectListItem {
  subject_id: string;
  MMSE: number;
  MOCA: number;
  CDR_global: number;
  CDR_SB: number;
  HIS: number;
  risk_probability: number;
  risk_level: string;
}

// 被试详情
export interface SubjectDetail {
  subject_id: string;
  scale_scores: ScaleScores;
  vr_summary: VRSummary;
  risk: RiskAssessment;
  explanations: string[];
}

// 相关性条目
export interface CorrelationItem {
  target: string;
  feature: string;
  feature_label: string;
  n: number;
  pearson_r: number;
  spearman_r: number;
  p_value: number;
  significant: boolean;
}

// 模型指标
export interface ModelMetrics {
  model_name: string;
  target: string;
  cv_method: string;
  metrics: {
    auc: number;
    accuracy: number;
    sensitivity: number;
    specificity: number;
    f1: number;
    precision: number;
    cv_mean_auc: number;
    cv_std_auc: number;
  };
  selected_features: string[];
  feature_importance: FeatureImportance[];
  training_date: string;
  sample_size: number;
}

// 特征权重
export interface FeatureImportance {
  feature: string;
  label: string;
  coefficient: number;
}
