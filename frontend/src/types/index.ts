// 从各个类型文件中导出所有类型
export * from './post';
export * from './category';
export * from './tag';
export * from './user';
export * from './auth';

// 通用响应接口
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 分页参数接口
export interface PaginationParams {
  page: number;
  page_size: number;
} 