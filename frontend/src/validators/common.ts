/**
 * 验证字符串是否不为空
 * @param value - 要验证的字符串
 * @returns 验证结果
 */
export function isNotEmpty(value: string): boolean {
  return !!value && value.trim() !== ''
}

/**
 * 验证字符串最小长度
 * @param value - 要验证的字符串
 * @param minLength - 最小长度
 * @returns 验证结果
 */
export function isMinLength(value: string, minLength: number): boolean {
  return !!value && value.length >= minLength
}

/**
 * 验证字符串最大长度
 * @param value - 要验证的字符串
 * @param maxLength - 最大长度
 * @returns 验证结果
 */
export function isMaxLength(value: string, maxLength: number): boolean {
  return !value || value.length <= maxLength
}

/**
 * 验证邮箱格式
 * @param value - 要验证的邮箱字符串
 * @returns 验证结果
 */
export function isValidEmail(value: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(value)
}

/**
 * 验证两个值是否相等
 * @param value1 - 第一个值
 * @param value2 - 第二个值
 * @returns 验证结果
 */
export function isEqual(value1: unknown, value2: unknown): boolean {
  return value1 === value2
} 