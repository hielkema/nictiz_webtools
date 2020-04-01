import Vue from 'vue'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import store from './store'
import * as d3 from "../node_modules/d3"
import vuetify from './plugins/vuetify';
import VueCookies from '../node_modules/vue-cookies'
import VueApexCharts from 'vue-apexcharts'
// import { alert } from './store/alert.module'
Vue.config.productionTip = false
Vue.prototype.$axios = axios

Vue.use(require('vue-cookies'));
Vue.use('VeeValidate');
Vue.component('apexchart', VueApexCharts)


// Add an axios interceptor for adding token to requests
axios.interceptors.request.use(function(config) {
  const storage = JSON.parse(localStorage.getItem('user'))
  const token = storage.access;

  if ( token != null ) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
}, function(err) {
  return Promise.reject(err);
});

// Add a response axios interceptor for expired tokens
axios.interceptors.response.use((response) => {
  return response
}, function (error) {
  const originalRequest = error.config;

  // alert(error.response.status)
  
  if (error.response.status === 403 && originalRequest.url === store.state.baseUrl+'jwtauth/token/') {
      router.push('/login');
      return Promise.reject(error);
  }

  if (error.response.status === 403 && !originalRequest._retry) {
    console.error('will try to refresh')
      originalRequest._retry = true;
      const tokenStorage = JSON.parse(localStorage.getItem('user'));
      // alert('Refreshtoken: '+ tokenStorage)
      return axios.post(store.state.baseUrl+'jwtauth/refresh/',
          {
              "refresh": tokenStorage.refresh
          })
          .then(res => {
              if (res.status === 200) {
                console.error('Got 200 on refresh req -> refreshing')
                const newTokenStorage = {
                  'access' : res.data.access,
                  'refresh' : tokenStorage.refresh
                }
                console.error('Setting localstorage to '+JSON.stringify(newTokenStorage))

                localStorage.setItem('user',JSON.stringify(newTokenStorage));
                axios.defaults.headers.common['Authorization'] = 'Bearer ' + newTokenStorage.access //res.data.access;
                return axios(originalRequest);
              }else{
                console.error('Got status '+res.status)
              }
          })
          .catch(error => {
            console.error('Uitgelogd: Error bij refresh '+Object.keys(error))
            localStorage.removeItem('user')
            store.state.authentication.status.loggedIn = false
            store.state.authentication.user = null
            router.push('login')
          })
  }else{
    console.error('Deze error? Raar.')
  }
  return Promise.reject(error);
});

new Vue({
  router,
  store,
  d3,
  VueCookies,
  vuetify,
  axios,
  render: h => h(App)
}).$mount('#app')
