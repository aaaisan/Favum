// 帖子基本信息接口
export interface Post {
  id: number;
  title: string;
  content: string;
  author_id: number;
  author_name: string;
  created_at: string;
  updated_at: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  is_favorite?: boolean;
}

// 帖子列表响应接口
export interface PostList {
  posts: Post[];
  total: number;
  page: number;
  page_size: number;
}

// 帖子创建请求接口
export interface PostCreateRequest {
  title: string;
  content: string;
  category_id?: number;
  tags?: string[];
}

// 帖子更新请求接口
export interface PostUpdateRequest {
  title?: string;
  content?: string;
  category_id?: number;
  tags?: string[];
} 