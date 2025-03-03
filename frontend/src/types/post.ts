import type { Category } from './category'
import type { Tag } from './tag'
import type { User } from './user'

// 帖子基本信息接口
export interface Post {
  id: number;
  title: string;
  content: string;
  author_id: number;
  section_id: number;
  category_id: number | null;
  created_at: string;
  updated_at: string;
  is_hidden: boolean;
  is_deleted: boolean;
  deleted_at: string | null;
  vote_count: number;
  author?: User;
  category?: Category;
  tags?: Tag[];
}

// 帖子列表响应接口
export interface PostList {
  posts: Post[];
  total: number;
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

// 投票类型
export type VoteType = 'upvote' | 'downvote';

// 投票响应接口
export interface VoteResponse {
  success: boolean;
  vote_count: number;
}

// 帖子投票记录接口
export interface PostVote {
  id: number;
  user_id: number;
  post_id: number;
  vote_type: VoteType;
  created_at: string;
} 