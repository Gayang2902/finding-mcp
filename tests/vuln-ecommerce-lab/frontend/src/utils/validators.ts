export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export function isValidPhone(phone: string): boolean {
  return /^\+?[\d\s\-().]{7,20}$/.test(phone)
}

export function isValidPassword(password: string): { valid: boolean; errors: string[] } {
  const errors: string[] = []
  if (password.length < 8) errors.push('At least 8 characters')
  if (!/[A-Z]/.test(password)) errors.push('At least one uppercase letter')
  if (!/[a-z]/.test(password)) errors.push('At least one lowercase letter')
  if (!/[0-9]/.test(password)) errors.push('At least one number')
  return { valid: errors.length === 0, errors }
}

export function isValidPostalCode(code: string): boolean {
  return /^\d{5}(-\d{4})?$/.test(code) || /^[A-Z]\d[A-Z] ?\d[A-Z]\d$/.test(code)
}

export function isValidCardNumber(number: string): boolean {
  const digits = number.replace(/\s/g, '')
  return /^\d{16}$/.test(digits)
}

export function isValidCardExpiry(expiry: string): boolean {
  return /^(0[1-9]|1[0-2])\/\d{2}$/.test(expiry)
}

export function isValidCVV(cvv: string): boolean {
  return /^\d{3,4}$/.test(cvv)
}
