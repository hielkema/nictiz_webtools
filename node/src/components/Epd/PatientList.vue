<template>
  <div>
    <v-card>
        <v-subheader>Patiënten</v-subheader>
          <v-list three-line>
            <v-list-item-group v-model="patients" color="primary">
              <v-list-item 
                three-line
                v-for="item in patients"
                :key="item.id"
                v-on:click="setCurrentPatient(item.id)"
              >
                <v-list-item-content>
                  <v-list-item-title>{{item.name.first}} ({{item.name.initials}}) {{item.name.last}}</v-list-item-title>
                  <v-list-item-subtitle>
                    <span>{{item.dob}}</span><br>
                    <span>{{item.id}}</span><br>
                    <v-divider></v-divider>
                  </v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list-item-group>
        </v-list>
    </v-card>
  </div>
</template>

<script>
export default {
  data() {
    return {
      search: '',
    }
  },
  methods: {
    setCurrentPatient: function (patientid) {
      this.$store.dispatch('Epd/getPatientData', patientid)
      this.$store.dispatch('Epd/getDecursus',patientid)
    }
  },
  computed: {
    patients(){
      return this.$store.state.Epd.patientList;
    },
    currentPatient(){
      return this.$store.state.Epd.currentPatient;
    }
  }
}
</script>