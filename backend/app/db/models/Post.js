const mongoose = require('mongoose');
const Schema = mongoose.Schema;

// 帖子模式
const PostSchema = new Schema({
  title: {
    type: String,
    required: [true, '标题不能为空'],
    trim: true,
    maxlength: [200, '标题最多200个字符']
  },
  content: {
    type: String,
    required: [true, '内容不能为空'],
  },
  author: {
    type: Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  category: {
    type: Schema.Types.ObjectId,
    ref: 'Category',
    default: null
  },
  tags: [{
    type: Schema.Types.ObjectId,
    ref: 'Tag'
  }],
  view_count: {
    type: Number,
    default: 0
  },
  vote_count: {
    type: Number,
    default: 0
  },
  is_hidden: {
    type: Boolean,
    default: false
  },
  is_deleted: {
    type: Boolean,
    default: false
  },
  is_sticky: {
    type: Boolean,
    default: false
  }
}, {
  timestamps: {
    createdAt: 'created_at', 
    updatedAt: 'updated_at'
  },
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// 虚拟属性：评论数
PostSchema.virtual('comments', {
  ref: 'Comment',
  localField: '_id',
  foreignField: 'post',
  justOne: false,
  count: false
});

// 索引
PostSchema.index({ title: 'text', content: 'text' });
PostSchema.index({ author: 1 });
PostSchema.index({ category: 1 });
PostSchema.index({ created_at: -1 });

// 添加view_count的方法
PostSchema.methods.incrementViewCount = async function() {
  this.view_count += 1;
  return this.save();
};

// 静态方法：获取热门帖子
PostSchema.statics.getHotPosts = function(limit = 5) {
  return this.find({ is_deleted: false, is_hidden: false })
    .sort({ view_count: -1 })
    .limit(limit)
    .populate('author', 'username avatar')
    .populate('category', 'name color');
};

// 查询钩子：自动填充作者和分类
PostSchema.pre('find', function() {
  this.populate('author', 'username avatar')
      .populate('category', 'name color')
      .populate('tags', 'name');
});

PostSchema.pre('findOne', function() {
  this.populate('author', 'username avatar')
      .populate('category', 'name color')
      .populate('tags', 'name');
});

module.exports = mongoose.model('Post', PostSchema); 