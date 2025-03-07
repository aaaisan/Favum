const mongoose = require('mongoose');
const Schema = mongoose.Schema;

// 评论模式
const CommentSchema = new Schema({
  content: {
    type: String,
    required: [true, '评论内容不能为空'],
    trim: true
  },
  user: {
    type: Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  post: {
    type: Schema.Types.ObjectId,
    ref: 'Post',
    required: true
  },
  parent: {
    type: Schema.Types.ObjectId,
    ref: 'Comment',
    default: null
  },
  likes: {
    type: Number,
    default: 0
  },
  is_deleted: {
    type: Boolean,
    default: false
  }
}, {
  timestamps: {
    createdAt: 'created_at', 
    updatedAt: 'updated_at'
  },
  toJSON: { virtuals: true }
});

// 虚拟属性：回复
CommentSchema.virtual('replies', {
  ref: 'Comment',
  localField: '_id',
  foreignField: 'parent',
  justOne: false
});

// 索引
CommentSchema.index({ post: 1, created_at: -1 }); // 获取帖子的评论，按时间排序
CommentSchema.index({ user: 1 }); // 获取用户的评论

// 查询钩子：自动填充用户信息
CommentSchema.pre('find', function() {
  this.populate('user', 'username avatar');
});

CommentSchema.pre('findOne', function() {
  this.populate('user', 'username avatar');
});

module.exports = mongoose.model('Comment', CommentSchema); 