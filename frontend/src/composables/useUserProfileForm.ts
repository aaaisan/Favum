import { ref } from 'vue'
import type { User, UserProfileForm, UserProfileFormErrors } from '../types/user'
import { validateUserProfileForm, clearUserProfileFormErrors } from '../validators/userProfile'

export function useUserProfileForm(user: User | null) {
  const form = ref<UserProfileForm>({
    username: user?.username || '',
    email: user?.email || '',
    bio: user?.bio || '',
    password: '',
    confirmPassword: ''
  })

  const errors = ref<UserProfileFormErrors>({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  })

  const isSubmitting = ref(false)
  const successMessage = ref('')

  const resetForm = () => {
    if (user) {
      form.value.username = user.username
      form.value.email = user.email
      form.value.bio = user.bio || ''
    }
    form.value.password = ''
    form.value.confirmPassword = ''
    clearUserProfileFormErrors(errors.value)
    successMessage.value = ''
  }

  const validate = () => {
    return validateUserProfileForm(form.value, errors.value)
  }

  return {
    form,
    errors,
    isSubmitting,
    successMessage,
    resetForm,
    validate
  }
} 