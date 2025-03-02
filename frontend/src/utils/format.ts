/**
 * 格式化日期为本地字符串
 * @param dateString - 日期字符串或undefined
 * @param defaultValue - 日期为空时的默认值，默认为"未知"
 * @returns 格式化后的日期字符串
 */
export function formatDate(dateString: string | undefined, defaultValue: string = '未知'): string {
  if (!dateString) return defaultValue
  try {
    const date = new Date(dateString)
    return date.toLocaleString()
  } catch (e) {
    console.error('日期格式化错误:', e)
    return defaultValue
  }
}

/**
 * 获取字符串的首字母（用于头像显示）
 * @param name - 姓名字符串或undefined
 * @param defaultValue - 字符串为空时的默认值，默认为"?"
 * @returns 首字母大写
 */
export function getInitials(name: string | undefined, defaultValue: string = '?'): string {
  if (!name || name.length === 0) return defaultValue
  return name.charAt(0).toUpperCase()
}

/**
 * 截断文本到指定长度
 * @param text - 要截断的文本
 * @param maxLength - 最大长度，默认为150
 * @returns 截断后的文本
 */
export function truncateText(text: string, maxLength: number = 150): string {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
} 