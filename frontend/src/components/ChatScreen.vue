<script setup>
import { ref, watch } from 'vue'
import { useAppStore } from '@/stores/useAppStore'

const store = useAppStore()
const prompt = ref(store.prompt)
const chunks = ref([])
const chunksDisplayed = ref(false)
const prevModel = ref('')
const prevPrompt = ref('')
const res = ref({})

watch(prompt, (newValue) => {
  store.setPrompt(newValue)
})

const handleRagRequest = () => {
  if (prompt.value === '') {
    return
  }

  const formData = new FormData()
  formData.append('json', store.toJson())

  if (store.getFile()) {
    formData.append('file', store.getFile())
  }

  const baseUrl = import.meta.env.VITE_BACKEND_URL

  prevPrompt.value = store.getPrompt()
  res.value = {}

  fetch(baseUrl + '/promptRag', {
    method: 'POST',
    body: formData
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Non 200 status code! ${response.status}`)
      }
      return response.json()
    })
    .then((data) => {
      prompt.value = ''
      prevModel.value = store.getModel()

      try {
        res.value = JSON.parse(data.response)
      } catch (e) {
        res.value = data.response
      }
      chunks.value = data.chunks.filter((chunk) => chunk.length > 0)
    })
    .catch(() => {
      console.log(`Error from RAG.`)
      res.value = 'An error occured while processing request, please try again.'
    })
}

const flipChunksDisplayed = () => {
  chunksDisplayed.value = !chunksDisplayed.value
}

const isEmpty = (value) => {
  if (typeof value === 'string') {
    return value.trim().length === 0
  } else if (typeof value === 'object') {
    return value && Object.keys(value).length === 0 && value.constructor === Object
  }
  return !value
}
</script>

<template>
  <div class="chat-screen">
    <div class="response-area">
      <div class="user-promptContainer">
        <div class="user-prompt" v-if="prevPrompt.length > 0">
          {{ prevPrompt }}
        </div>
      </div>
      <div v-if="!isEmpty(res)" class="rag-prompt">
        <h3>
          {{ prevModel }}
          <a @click="flipChunksDisplayed" v-if="chunks !== null && chunks.length > 0">
            <span> - </span>
            <span v-if="!chunksDisplayed">View Chunks</span>
            <span v-else>Close Chunks</span>
          </a>
        </h3>

        <div v-if="chunksDisplayed && chunks !== null && chunks.length > 0" class="ChunkDisplay">
          <ol class="chunk-list">
            <li v-for="chunk in chunks" :key="chunk">{{ chunk }}</li>
          </ol>
        </div>

        <div v-if="typeof res === 'object'">
          <div v-for="(value, key) in Object.entries(res)" :key="key">
            <hr />
            <h4>{{ value[0] }}</h4>
            <ul>
              <li v-for="(subValue, subKey) in Object.entries(value[1])" :key="subKey">
                {{ subValue[0] }}: {{ subValue[1] }}
              </li>
            </ul>
          </div>
        </div>
        <div v-else>
          {{ res }}
        </div>
      </div>
    </div>
    <div class="prompt-area">
      <textarea
        v-model="prompt"
        @keydown.enter.prevent="handleRagRequest"
        placeholder="Enter a prompt here"
        id="TextArea"
      ></textarea>

      <div class="submit-container">
        <button @click="handleRagRequest" id="SubmitButton">
          <img src="@/assets/up-arrow-icon.svg" alt="Submit Prompt" width="25" height="25" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.response-area {
  flex-grow: 1;
  padding: 20px;
  margin-bottom: 20px;
  overflow-y: auto;
  overflow-x: hidden;
}

.prompt-area {
  border: 1px solid #ccc;
  padding: 20px;
  background-color: #e6e6e6;
  min-height: 90px;
  display: flex;
  border-radius: 25px;
}

.chat-screen {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

#TextArea {
  width: 95%;
  height: 100%;
  margin: 0;
  font-size: 18px;
  outline: none;
  border: none;
  background: transparent;
  box-shadow: none;
  resize: none;
}

#SubmitButton {
  width: 50px;
  height: 50px;
  border-radius: 30px;
}

.submit-container {
  display: flex;
  align-items: center;
}

.chunk-list li {
  padding: 10px;
}

a {
  text-decoration: underline;
  font-size: 12px;
  cursor: pointer;
}

a:hover {
  color: #0062ff;
}

.user-prompt {
  background-color: #ccc;
  border-radius: 20px;
  padding: 15px;
  overflow-wrap: break-word;
  margin-left: auto;
  text-align: right;
  display: inline-block;
}

.rag-prompt {
  background-color: #ccc;
  border-radius: 20px;
  padding: 5px 15px;
  overflow-wrap: break-word;
  margin-top: 30px;
  max-width: 70%;
}

.user-promptContainer {
  display: flex;
  justify-content: flex-end;
  width: 100%;
  background-color: #f0f0f0;
}

.user-prompt {
  max-width: 70%;
  width: fit-content;
  background-color: #d3d3d3;
  padding: 10px 20px;
  border: 1px solid #ccc;
}
</style>
