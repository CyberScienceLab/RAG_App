<script setup>
import { useAppStore } from '@/stores/useAppStore'
import { ref, onMounted } from 'vue'

const store = useAppStore()

const models = ref([])
const ragTypes = ref([])
const chunks = ref(store.getChunks())
const selectedModel = ref(store.getModel())
const selectedRagTypes = ref(store.getRagTypes())

const handleModelChange = () => {
  store.setRagConfig('model', selectedModel)
}

const handleRagTypesChange = () => {
  store.setRagConfig('ragTypes', selectedRagTypes)
}

const handleChunksChange = () => {
  store.setRagConfig('chunks', chunks)
}

const handleFileChange = (event) => {
  const file = event.target.files[0]

  if (file) {
    store.setFile(file)
  } else {
    store.setFile(null)
  }
}

onMounted(async () => {
  try {
    const baseUrl = import.meta.env.VITE_BACKEND_URL
    const response = await fetch(`${baseUrl}/retrieveRagConfig`)
    const data = await response.json()

    models.value = data.models
    ragTypes.value = data.ragTypes
  } catch (err) {
    console.error('Error retrieving RAG config:', err)
  }
})
</script>

<template>
  <div>
    <h3 class="title">RAG Config</h3>

    <hr />

    <div class="config">
      <div class="container">
        <label for="modelDropdown">Model</label>
        <div class="input-wrapper">
          <select v-model="selectedModel" @change="handleModelChange" id="modelDropdown">
            <option v-for="model in models" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
        </div>
      </div>

      <div class="container">
        <label for="ragTypesDropdown">RAG Types</label>
        <div class="input-wrapper">
          <select
            v-model="selectedRagTypes"
            multiple
            @change="handleRagTypesChange"
            id="ragTypesDropdown"
          >
            <option v-for="ragType in ragTypes" :key="ragType" :value="ragType">
              {{ ragType }}
            </option>
          </select>
        </div>
      </div>

      <div class="container">
        <label for="chunkInput"># of Relevant Context Used</label>
        <div class="input-wrapper">
          <input
            type="number"
            v-model="chunks"
            min="1"
            max="10"
            step="1"
            @input="handleChunksChange"
            id="chunkInput"
          />
        </div>
      </div>
    </div>

    <hr />

    <div class="file-upload">
      <div class="container">
        <label for="fileUpload">File Upload</label>
        <div class="input-wrapper">
          <!-- TODO: make this look nice -->
          <input type="file" @change="handleFileChange" accept=".pdf,.txt" id="fileUpload" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  color: #5d5d5d;
}

.title {
  text-align: center;
}

hr {
  border: 0;
  height: 3px;
  background: #5d5d5d;
  margin: 20px 0 0;
}

.config,
.file-upload {
  padding: 20px;
}

.container {
  margin: 20px 0;
}

.input-wrapper {
  width: 200px;
}

.input-wrapper select,
.input-wrapper input {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px 15px;
  width: 100%;
  font-size: 16px;
  color: #333;
  box-sizing: border-box;
}

#chunkInput {
  width: 100%;
}
</style>
