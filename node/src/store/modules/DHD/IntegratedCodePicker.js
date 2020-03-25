import axios from 'axios'
// import { jwtHeader } from '@/helpers';
// import Vue from 'vue'
// import router from '@/router/index.js' //or whatever your router.js path is

const state = {
    searchResults: {
      'results': [],
    },
    currentConcept: false,
    children: [],
    parents: [],
    loading: {
      'searchResults' : false,
      'children' : false,
      'concept' : false,
      'parents' : false, 
    }
  }

  //// ---- Mutations
  const mutations = {
    setResults: (state, payload) => {
      state.searchResults = payload
      state.loading.searchResults = false
    },
    setCurrentConcept: (state, payload) => {
      state.currentConcept = payload
      state.loading.concept = false
    },
    setChildren: (state, payload) => {
      state.children = payload
      state.loading.children = false
    },
    setParents: (state, payload) => {
      state.parents = payload
      state.loading.parents = false
    },
  }

  //// ---- Actions
  const actions = {
    // Get results
    search: (context, term) => {
      state.loading.searchResults = true
      state.currentConcept = false
      axios
      .get(context.rootState.baseUrl+'dhd/search/'+term+'/')
      .then((response) => {
        // alert('Respons getResults: '+response.data)
        context.commit('setResults',response.data)
        return true;
      })
    },
    // Fetch specific concept
    getConcept: (context, conceptid) => {
      state.loading.concept = true
      axios
      .get(context.rootState.baseUrl+'dhd/concept/'+conceptid+'/')
      .then((response) => {
        // alert('Respons getResults: '+response.data)
        context.commit('setCurrentConcept',response.data)
        return true;
      })
    },
    // Fetch children
    getChildren: (context, conceptid) => {
      state.loading.children = true
      axios
      .get(context.rootState.baseUrl+'dhd/children/'+conceptid+'/')
      .then((response) => {
        // alert('Respons getResults: '+response.data)
        context.commit('setChildren',response.data.children)
        return true;
      })
    },
    // Fetch parents
    getParents: (context, conceptid) => {
      state.loading.parents = true
      axios
      .get(context.rootState.baseUrl+'dhd/parents/'+conceptid+'/')
      .then((response) => {
        // alert('Respons getResults: '+response.data)
        context.commit('setParents',response.data.parents)
        return true;
      })
    },
  }

export default {
    namespaced: true,
    state,
    // getters,
    actions,
    mutations
}