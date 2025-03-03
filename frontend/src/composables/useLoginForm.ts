import { reactive, ref } from 'vue'
import type { LoginForm, LoginFormErrors } from '../types'
import { validateLoginForm, clearLoginFormErrors } from '../validators/login'

export function useLoginForm() {
  const form = reactive<LoginForm>({
    email: '',
    password: ''
  })

  const errors = reactive<LoginFormErrors>({
    email: '',
    password: ''
  })

  const isSubmitting = ref(false)
  const errorMessage = ref('')

  const resetForm = () => {
    form.email = ''
    form.password = ''
    clearLoginFormErrors(errors)
    errorMessage.value = ''
  }

  const validate = () => {
    return validateLoginForm(form, errors)
  }

  return {
    form,
    errors,
    isSubmitting,
    errorMessage,
    resetForm,
    validate
  }
} 