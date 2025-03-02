// 评论基本信息接口
export interface Comment {
  id: number;
  content: string;
  post_id: number;
  author_id: number;
  author_name: string;
  created_at: string;
  updated_at?: string;
  parent_id?: number;
  like_count: number;
}

// 评论列表响应接口
export interface CommentList {
  comments: Comment[];
  total: number;
  page: number;
  page_size: number;
}

// 评论创建请求接口
export interface CommentCreateRequest {
  content: string;
  post_id: number;
  parent_id?: number;
} 