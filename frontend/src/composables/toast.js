import { ref } from 'vue'

const _toast = ref(null)

export function setToastRef(toastRef) { _toast.value = toastRef.value }
export function useToast() {
  return {
    success: (msg) => _toast.value?.show(msg, 'success'),
    warning: (msg) => _toast.value?.show(msg, 'warning'),
    error:   (msg) => _toast.value?.show(msg, 'error'),
  }
}
