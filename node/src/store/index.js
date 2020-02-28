import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

import Epd from './modules/Epd'
import TermspaceComments from './modules/Terminologie/TermspaceComments'
import MappingComments from './modules/Terminologie/MappingComments'

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
      MappingComments,
      authentication,
      alert,
  },
  actions: {
    getPermissions: (context) => {
      axios
      .get(context.state.baseUrl+'termspace/component_api/74400008/')
    }
  }
})
