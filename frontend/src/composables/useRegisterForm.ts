import { reactive, ref } from 'vue'
import type { RegisterForm, RegisterFormErrors } from '../types/auth'
import { validateRegisterForm, clearRegisterFormErrors } from '../validators/register'

export function useRegisterForm() {
  const form = reactive<RegisterForm>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    bio: ''
  })

  const errors = reactive<RegisterFormErrors>({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  })

  const isSubmitting = ref(false)
  const successMessage = ref('')
  const errorMessage = ref('')

  const resetForm = () => {
    form.username = ''
    form.email = ''
    form.password = ''
    form.confirmPassword = ''
    form.bio = ''
    clearRegisterFormErrors(errors)
    successMessage.value = ''
    errorMessage.value = ''
  }

  const validate = () => {
    return validateRegisterForm(form, errors)
  }

  return {
    form,
    errors,
    isSubmitting,
    successMessage,
    errorMessage,
    resetForm,
    validate
  }
} 