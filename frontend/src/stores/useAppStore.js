import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    // Default values
    prompt: '',
    ragConfig: {
      model: 'Llama3',
      ragTypes: [],
      chunks: 5
    },
    file: null
  }),
  actions: {
    setRagConfig(key, value) {
      this.ragConfig[key] = value
    },
    setPrompt(prompt) {
      this.prompt = prompt
    },
    setFile(file) {
      this.file = file
    },
    toJson() {
      // excludes the file since that will be added as a file in formData
      return JSON.stringify({
        prompt: this.prompt,
        ragConfig: this.ragConfig,
      })
    },
    getPrompt() {
      return this.prompt
    },
    getModel() {
      return this.ragConfig['model']
    },
    getRagTypes() {
      return this.ragConfig['ragTypes']
    },
    getChunks() {
      return this.ragConfig['chunks']
    },
    getFile() {
      return this.file
    }
  }
})
