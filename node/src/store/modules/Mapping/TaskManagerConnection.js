import axios from 'axios'
// import Vue from 'vue'

const state = {
    tasks: [],
    loading: false,
  }

  //// ---- Mutations
  const mutations = {
    setTasks: (state, payload) => {
      state.tasks = payload
    },
  }

  //// ---- Actions
  const actions = {
    getTasks: (context) => {
      // context.state.RcRules = {}
      context.state.loading = true
      axios
      .get(context.rootState.baseUrl+'mapping/api/1.0/tasks/')
      .then((response) => {
          console.log(response.data)
          context.commit('setTasks',response.data)
          context.state.loading = false
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