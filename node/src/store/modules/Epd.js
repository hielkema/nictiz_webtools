import axios from '../../../node_modules/axios'
import Vue from 'vue'

const state = {
    currentPatient: {},
    patientList: [],
    currentPatientDecursus: [],
    dialogDecursusData: {},
    output: ''
  }

  //// ---- Mutations
  const mutations = {
    getPatientList: (state, payload) => {
      state.patientList = payload
    },
    getPatientData: (state, payload) => {
      state.currentPatient = payload[0]
    },
    getDecursusData: (state, payload) => {
      state.currentPatientDecursus = payload
    },
    getDecursusDetail: (state, payload) => {
      state.dialogDecursusData = payload
    },
    setCsrftoken: (state, payload) => {
      state.csrftoken = payload
    }
  }

  //// ---- Actions
  const actions = {
    // Get new CSRF token
    getCsrfToken: (context) => {
      axios
      .get(context.rootState.baseUrl+'epd/test/')
      .then((response) => {
        context.commit('setCsrftoken',response.data)
        return true;
      })
    },
    // Get patient-list
    getPatientList: (context) => {
      axios
      .get(context.rootState.baseUrl+'epd/patient/')
      .then((response) => {
        context.commit('getPatientList',response.data)
        return true;
      })
    },
    // Get patient-detail
    getPatientData: (context, patientid) => {
      axios
      .get(context.rootState.baseUrl+'epd/patient/'+patientid)
      .then((response) => {
        context.commit('getPatientData',response.data)
        return true;
      })
    },
    // Get decursus
    getDecursus: (context, patientid) => {
      axios
      .get(context.rootState.baseUrl+'epd/decursus/'+patientid)
      .then((response) => {
        context.commit('getDecursusData',response.data) 
        return true;
      })
    },
    // Get single decursus
    getDecursusDetail: (context, decursusId) => {
      axios
      .get(context.rootState.baseUrl+'epd/decursus/'+context.state.currentPatient.id+'/'+decursusId)
      .then((response) => {
        context.commit('getDecursusDetail',response.data)
        return true;
      })
    },
    // Add new decursus
    newDecursus: (context, patientid) => {
      const auth = {
        headers: {'X-CSRFToken' : Vue.$cookies.get('csrftoken')},
        withCredentials: true
      }
      axios
      .post(context.rootState.baseUrl+'epd/decursus/', {
        'action'    : 'new',
        'patientId' : patientid
      },auth)
      .then(response => {
        context.dispatch('getDecursus',response.data.patientid)
        }
      )
    },
    postProblem: (context, payload) => {
      const auth = {
        headers: {'X-CSRFToken' : Vue.$cookies.get('csrftoken')},
        withCredentials: true
      }
      axios
      .post(context.rootState.baseUrl+'epd/problem/', {
        'action'   : payload.action,
        'decursusId'   : payload.decursusId,
        'patientId'   : payload.patientId,
        'problem' : payload.problem
      },auth)
      .then(response => {
        // console.log('Updating data for pt '+response.data.patientid+' after response '+response.data)
        context.dispatch('getPatientData',response.data.patientid)
        context.dispatch('getDecursus',response.data.patientid)
        return true;
      })
    },
    // Post problem data
    // Post decursus data
    postDecursus: (context, payload) => {
      const auth = {
        headers: {'X-CSRFToken' : Vue.$cookies.get('csrftoken')},
        withCredentials: true
      }
      axios
      .post(context.rootState.baseUrl+'epd/decursus/', {
        'action'   : payload.action,
        'patientId'   : payload.decursus.patientid,
        'decursus' : payload.decursus
      },auth)
      .then(response => {
        console.log('Updating data for pt '+response.data.patientid+' after response '+response.data)
        context.dispatch('getPatientData',response.data.patientid)
        context.dispatch('getDecursus',response.data.patientid)
        return true;
      })
    },
    // Delete decursus
    deleteDecursus: (context, payload) => {
      const auth = {
        headers: {'X-CSRFToken' : Vue.$cookies.get('csrftoken')},
        withCredentials: true
      }
      axios
      .post(context.rootState.baseUrl+'epd/decursus/', {
        'action'   : 'delete',
        'decursusId'   : payload,
        'patientId'   : context.state.currentPatient.id
      },auth)
      .then(response => {
          console.log('Updating data for pt '+context.state.currentPatient.id+' after response '+response),
          context.dispatch('getPatientData',context.state.currentPatient.id),
          context.dispatch('getDecursus',context.state.currentPatient.id)
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