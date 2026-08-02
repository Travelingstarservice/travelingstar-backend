import { createApp } from 'vue';
import App from './App.vue';
import router from './router/index.js';
import axios from 'axios';
import './style.css';

const app = createApp(App);

app.config.globalProperties. = axios;

app.use(router);
app.mount('#app');

if __name__ == "__main__":
    app.run(...)
