import axios from 'axios'
// import { jwtHeader } from '@/helpers';
// import Vue from 'vue'
// import router from '@/router/index.js' //or whatever your router.js path is

const state = {
    searchTerm: '',
    results: [],
    numResults: 0,
  }

  //// ---- Mutations
  const mutations = {
    setResults: (state, payload) => {
      state.results = payload.results
      state.searchTerm = payload.searchterm
      state.numResults = payload.num_results
    }
  }

  //// ---- Actions
  const actions = {
    // Get results
    getResults: (context, term) => {
      axios
      .get(context.rootState.baseUrl+'termspace/search_comments/'+term+'/')//,{'headers':jwtHeader()})
      .then((response) => {
        // alert('Respons getResults: '+response.data)
        context.commit('setResults',response.data)
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