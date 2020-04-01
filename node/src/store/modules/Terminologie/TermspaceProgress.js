import axios from 'axios'
// import { jwtHeader } from '@/helpers';
// import Vue from 'vue'
// import router from '@/router/index.js' //or whatever your router.js path is

const state = {
    results: [],
  }

  //// ---- Mutations
  const mutations = {
    setProgress: (state, payload) => {
      state.results = payload
    }
  }

  //// ---- Actions
  const actions = {
    // Get results
    // getResults: (context, term) => {
    getProgress: (context) => {
      axios
      .get(context.rootState.baseUrl+'termspace/fetch_termspace_tasksupply/')
      .then((response) => {
        // alert('Respons getResults: '+response.data)
        context.commit('setProgress',response.data)
        return true;
      })
    }
  }

export default {
    namespaced: true,
    state,
    // getters,
    actions,
    mutations
}