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
  view_count?: number;
  reply_count?: number;
  like_count?: number;
  is_liked?: boolean;
  is_favorite?: boolean;
  category_name?: string;
  author?: User;
  category?: Category;
  tags?: Tag[];
  comments?: Comment[];
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

// 发帖表单类型
export interface PostForm {
  title: string;
  content: string;
  category_id: number;
  tags: string[];
  captcha_id: string;
  captcha_code: string;
}

// 发帖表单错误类型
export interface PostFormErrors {
  title: string;
  content: string;
  category_id: string;
  captcha_code: string;
}

// 回复表单类型
export interface ReplyForm {
  content: string;
  post_id: number;
  parent_id?: number;
  captcha_id: string;
  captcha_code: string;
}

// 回复表单错误类型
export interface ReplyFormErrors {
  content: string;
  captcha_code: string;
}

// 回复类型
export interface Reply {
  id: number;
  content: string;
  post_id: number;
  parent_id?: number;
  author: User;
  created_at: string;
  updated_at: string;
  like_count: number;
  is_liked: boolean;
  children?: Reply[];
}

// 论坛分类类型
export interface ForumCategory {
  id: number;
  name: string;
  description: string;
  post_count: number;
}

// 论坛标签类型
export interface ForumTag {
  id: number;
  name: string;
  post_count: number;
}

// 评论类型
export interface Comment {
  id: number;
  content: string;
  post_id: number;
  user_id: number;
  user?: User;
  created_at: string;
  updated_at: string;
} 