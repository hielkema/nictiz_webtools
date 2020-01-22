import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

import Epd from './modules/Epd'
import TermspaceComments from './modules/Terminologie/TermspaceComments'

Vue.use(Vuex)
Vue.use(axios)

export default new Vuex.Store({
  modules: {
      Epd,
      TermspaceComments
  }
})
