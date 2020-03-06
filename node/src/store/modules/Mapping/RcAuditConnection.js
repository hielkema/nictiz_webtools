import axios from 'axios'
import Vue from 'vue'

const state = {
    baseUrl: 'http://localhost/',
    // baseUrl: 'https://termservice.test-nictiz.nl/',
    RcRules: {},
    RcList: [],
    selectedRc: null,
    loading: false,
  }

  //// ---- Mutations
  const mutations = {
    setRcRules: (state, payload) => {
      state.RcRules = payload
    },
    setRcs: (state, payload) => {
      state.RcList = payload
    }
  }

  //// ---- Actions
  const actions = {
    getRcRules: (context, rc_id) => {
      // context.state.RcRules = {}
      context.state.loading = true
      axios
      .get(context.state.baseUrl+'mapping/api/1.0/export_rc_rules/'+ rc_id + '/')
      .then((response) => {
          console.log(response.data)
          context.commit('setRcRules',response.data)
          context.state.selectedRc = rc_id
          context.state.loading = false
          return true;
      })
    },
    getRcs: (context) => {
      axios
      .get(context.state.baseUrl+'mapping/api/1.0/export_rcs/')
      .then((response) => {
          context.commit('setRcs',response.data)
          return true;
      })
    },
    pullRulesFromDev: (context, payload) => {
      const auth = {
        headers: {'X-CSRFToken' : Vue.$cookies.get('csrftoken')},
        withCredentials: true
      }
      axios
      .post(context.state.baseUrl+'mapping/api/1.0/export_rc_rules/', {
        'selection' : 'component',
        'id' : payload.component_id,
        'codesystem' : payload.codesystem,
        'rc_id' : context.state.selectedRc
      },auth)
      .then(() => {
        context.dispatch('getRcRules',context.state.selectedRc)
        return true;
        }
      )
    },
    postRuleReview: (context, payload) => {
      const auth = {
        headers: {'X-CSRFToken' : Vue.$cookies.get('csrftoken')},
        withCredentials: true
      }
      axios
      .post(context.state.baseUrl+'mapping/api/1.0/rc_rule_review/', {
        'action' : payload.action,
        'component_id' : payload.component_id,
        'rc_id' : payload.rc_id
      },auth)
      .then(() => {
        context.dispatch('getRcRules',context.state.selectedRc)
        return true;
        }
      )
    }
  }

export default {
    namespaced: true,
    state,
    // getters,
    actions,
    mutations
}