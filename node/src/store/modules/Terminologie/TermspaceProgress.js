import axios from 'axios'
// import { jwtHeader } from '@/helpers';
// import Vue from 'vue'
// import router from '@/router/index.js' //or whatever your router.js path is

const state = {
    ProgressPerStatus_table: [],
    ProgressPerStatus_graph: {
        'series' : [],
    },
    ProgressPerUser: {
        'series' : [],
    },
  }

  //// ---- Mutations
  const mutations = {
    setProgressPerStatus_table: (state, payload) => {
      state.ProgressPerStatus_table = payload.progress
    },
    setProgressPerStatus_graph: (state, payload) => {
        state.ProgressPerStatus_graph = payload.progress
    },
    setProgressPerUser: (state, payload) => {
        state.ProgressPerUser = payload.progress
    }
  }

  //// ---- Actions
  const actions = {
    // Get results
    // getResults: (context, term) => {
    getProgressPerStatus: (context) => {
      axios
      .get(context.rootState.baseUrl+'termspace/fetch_termspace_tasksupply/')
      .then((response) => {
        // alert('Respons getResults: '+response.data)
        context.commit('setProgressPerStatus_table',response.data)
        return true;
      })
    },
    getProgressPerStatusV2: (context) => {
        axios
        .get(context.rootState.baseUrl+'termspace/fetch_termspace_tasksupply_v2/')
        .then((response) => {
          // alert('Respons getResults: '+response.data)
          context.commit('setProgressPerStatus_graph',response.data)
          return true;
        })
    },
    getProgressPerUser: (context) => {
      axios
      .get(context.rootState.baseUrl+'termspace/fetch_termspace_user_tasksupply/all/')
      .then((response) => {
        // alert('Respons getResults: '+response.data)
        context.commit('setProgressPerUser',response.data)
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