import axios from 'axios'
// import Vue from 'vue'

const state = {
    // baseUrl: 'http://localhost/',
    baseUrl: 'https://termservice.test-nictiz.nl/',
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
      .get(context.state.baseUrl+'termspace/api/search_comments/'+term+'/')
      .then((response) => {
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