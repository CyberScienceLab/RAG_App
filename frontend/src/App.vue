<script setup>
import ChatScreen from './components/ChatScreen.vue'
import SideBar from './components/SideBar.vue'
</script>

<template>
  <div class="body">
    <SideBar class="side-bar" />
    <ChatScreen class="main-screen" />
  </div>
</template>

<style scoped>
.body {
  font-family: Arial, Helvetica, sans-serif;
  margin: 0;
  padding: 0;
  display: flex;
  height: 97vh;
  width: 98vw;
  background-color: #f1f1f1;
}

.side-bar {
  width: 25%;
  background-color: #d3d3d3;
  padding: 20px;
  box-sizing: border-box;
}

.main-screen {
  width: 75%;
  padding: 20px;
}

.header {
  font-weight: bold;
  margin-bottom: 10px;
  display: block;
}
</style>
