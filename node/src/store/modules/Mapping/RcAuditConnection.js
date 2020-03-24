import axios from 'axios'
import Vue from 'vue'

const state = {
    RcRules: {},
    RcList: [],
    selectedRc: null,
    loading: false,
    FHIRconceptMaps: false,
  }

  //// ---- Mutations
  const mutations = {
    setRcRules: (state, payload) => {
      state.RcRules = payload
    },
    setRcs: (state, payload) => {
      state.RcList = payload
    },
    setFHIRconceptMaps: (state, payload) => {
      state.FHIRconceptMaps = payload
    }
  }

  //// ---- Actions
  const actions = {
    getRcRules: (context, rc_id) => {
      // context.state.RcRules = {}
      context.state.loading = true
      axios
      .get(context.rootState.baseUrl+'mapping/api/1.0/export_rc_rules/'+ rc_id + '/')
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
      .get(context.rootState.baseUrl+'mapping/api/1.0/export_rcs/')
      .then((response) => {
          context.commit('setRcs',response.data)
          return true;
      })
    },
    getFHIRconceptMaps: (context, rc_id) => {
      axios
      .get(context.rootState.baseUrl+'mapping/api/1.0/fhir_conceptmap_list/'+rc_id+'/')
      .then((response) => {
          context.commit('setFHIRconceptMaps',response.data)
          return true;
      })
    },
    pullRulesFromDev: (context, payload) => {
      const auth = {
        headers: {'X-CSRFToken' : Vue.$cookies.get('csrftoken')},
        withCredentials: true
      }
      axios
      .post(context.rootState.baseUrl+'mapping/api/1.0/export_rc_rules/', {
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
    massPullChanges: (context) => {
      const auth = {
        headers: {'X-CSRFToken' : Vue.$cookies.get('csrftoken')},
        withCredentials: true
      }
      axios
      .post(context.rootState.baseUrl+'mapping/api/1.0/export_rc_rules/', {
        'selection' : 'codesystem',
        'rc_id' : context.state.selectedRc
      },auth)
      .then(() => {
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
      .post(context.rootState.baseUrl+'mapping/api/1.0/rc_rule_review/', {
        'action' : payload.action,
        'component_id' : payload.component_id,
        'rc_id' : payload.rc_id
      },auth)
      .then(() => {
        context.dispatch('getRcRules',context.state.selectedRc)
        return true;
        }
      )
    },
    createCacheSelectedRc: (context, payload) => {
      const auth = {
        headers: {'X-CSRFToken' : Vue.$cookies.get('csrftoken')},
        withCredentials: true
      }
      axios
      .post(context.rootState.baseUrl+'mapping/api/1.0/rc_export_fhir_json/', {
        'action' : 'save',
        'rc_id' : payload
      },auth)
      .then(() => {
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