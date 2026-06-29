import { create } from 'zustand'

interface UploadState {
  isUploading: boolean
  progress: number
  currentFile: string | null
  startUpload: (filename: string) => void
  updateProgress: (progress: number) => void
  completeUpload: () => void
  failUpload: () => void
}

export const useUploadStore = create<UploadState>((set) => ({
  isUploading: false,
  progress: 0,
  currentFile: null,
  startUpload: (filename) => set({ isUploading: true, progress: 0, currentFile: filename }),
  updateProgress: (progress) => set({ progress }),
  completeUpload: () => set({ isUploading: false, progress: 100, currentFile: null }),
  failUpload: () => set({ isUploading: false, progress: 0, currentFile: null }),
}))
