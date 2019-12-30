import Vue from 'vue'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify';
import VueCookies from '../node_modules/vue-cookies'
Vue.config.productionTip = false
Vue.prototype.$axios = axios

Vue.use(require('vue-cookies'));

new Vue({
  router,
  store,
  VueCookies,
  vuetify,
  axios,
  render: h => h(App)
}).$mount('#app')
