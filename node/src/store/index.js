import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

import Epd from './modules/Epd'
import TermspaceComments from './modules/Terminologie/TermspaceComments'
import { authentication } from './authentication.module';
import { alert } from './alert.module';
// import { userService } from '@/services';
// import router from '@/router/index.js';

Vue.use(Vuex)
Vue.use(axios)


export default new Vuex.Store({
  state: {
    baseUrl: 'https://termservice.test-nictiz.nl/',
  },
  modules: {
      Epd,
      TermspaceComments,
      authentication,
      alert,
  }
})
