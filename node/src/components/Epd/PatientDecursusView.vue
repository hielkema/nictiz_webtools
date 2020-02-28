<template>
  <div>
    <v-card v-if="currentPatient.id != null">
        <v-card-title>#{{currentPatient.id}}, {{currentPatient.name.first}} ({{currentPatient.name.initials}}) {{currentPatient.name.last}} - {{currentPatient.dob}}</v-card-title>
        <v-subheader>
          <span>{{currentPatient.address.street}}, {{currentPatient.address.city}}, {{currentPatient.address.country}}</span>
        </v-subheader>
        <span>
          <v-btn
            color="primary"
            dark
            @click="addNewDecursus()"
          >
            Nieuwe decursus
          </v-btn>
        </span>
    </v-card>
    
    <v-divider></v-divider>

    Decursus
<!-- List decursus items -->
    <v-container >
      <v-row v-bind:key="item.id" v-for="item in currentPatientDecursus">
        <v-card width="100%" style="margin-bottom:5px">
          <v-card-title>{{item.date}}</v-card-title>
          <v-card-text style="white-space: pre-line;">
            {{item.anamnese}}
            <li v-for="problem in item.problems" v-bind:key="problem.id">
              {{problem.type}} => {{problem.status}}: {{problem.naam}} [{{problem.begin}} t/m {{problem.eind}}] - {{problem.verificatie}}
            </li>
            
            <div style="float:right">
              <!-- {{item.edited}} -->
              <v-btn
                color="primary"
                dark
                @click="openEditDialogDecursus(item.id)"
              >
                Bewerken
              </v-btn>
              <v-btn
                color="warning"
                dark
                @click="deleteDecursusDialog(item.id)"
              >
                Verwijderen
              </v-btn>
              <v-menu
                bottom
                offset-y
              >
                <template v-slot:activator="{ on }">
                  <v-btn
                    class="ma-2"
                    v-on="on"
                  >Vastleggen</v-btn>
                </template>
                <v-list>
                  <v-list-item>
                    <v-btn
                      color="primary"
                      dark
                      @click="openAddDialogProblem(item.id)"
                    >
                      Verrichting
                    </v-btn>
                  </v-list-item>
                  <v-list-item>
                    <v-btn
                      color="primary"
                      dark
                      @click="dialog2 = true"
                    >
                      Diagnose
                    </v-btn>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
          </v-card-text>
        </v-card>
      </v-row>
    </v-container>
    
<!-- Dialog edit decursus -->
    <v-container>
      <v-dialog v-model="dialogDecursus" persistent max-width="900px">
        <v-card>
          <v-card-title>
            <span class="headline">Decursus</span>
          </v-card-title>
          <v-card-text>
            <v-container>
              <v-row>
                  <v-textarea
                    name="anamnese"
                    filled
                    label="Anamnese*"
                    auto-grow
                    persistent-label
                    v-model="dialogDecursusData.anamnese"
                  ></v-textarea>
              </v-row>
            </v-container>
            <small>*verplichte velden</small>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="blue darken-1" text @click="dialogDecursus = false">Close</v-btn>
            <v-btn color="blue darken-1" text @click="saveDialogDecursus()">Save</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-container>

<!-- Dialog delete decursus -->
    <v-container>
      <v-dialog v-model="dialogDeleteDecursus" persistent max-width="300px">
        <v-card>
          <v-card-title>
            <span class="headline">Verwijder decursus</span>
          </v-card-title>
          <v-card-text>
            <v-container>
              <v-row>
                Deze actie verwijdert de decursus en alle bijbehorende registraties
              </v-row>
            </v-container>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="blue darken-1" text @click="dialogDeleteDecursus = false">Behouden</v-btn>
            <v-btn color="blue darken-1" text @click="deleteDecursus()">Verwijderen</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-container>

<!-- Dialog add Problem -->
    <v-container>
      <v-dialog v-model="dialogProblem" persistent max-width="900px">
        <v-card>
          <v-card-title>
            <span class="headline">Probleem</span>
          </v-card-title>
          <v-card-text>
            <v-container>
              <v-row>
                <v-col>
                  <v-select
                    :items="problemTypes"
                    label="Probleemtype"
                    v-model="dialogProblemData.type"
                    dense
                    outlined
                  ></v-select>
                </v-col>
                <v-col>
                  <v-select
                    :items="['Actueel','Niet actueel']"
                    label="Status"
                    v-model="dialogProblemData.status"
                    dense
                    outlined
                  ></v-select>
                </v-col>
                <v-col>
                  <v-select
                    :items="['Werkdiagnose','Differentiaaldiagnose','Aangetoond','Uitgesloten','Onbekend']"
                    label="Verificatie"
                    v-model="dialogProblemData.verificatie"
                    dense
                    outlined
                  ></v-select>
                </v-col>
              </v-row>
              <v-row>
                <v-col>
                  <v-menu
                    v-model="beginpicker"
                    :close-on-content-click="false"
                    :nudge-right="40"
                    transition="scale-transition"
                    offset-y
                    min-width="290px"
                  >
                    <template v-slot:activator="{ on }">
                      <v-text-field
                        v-model="dialogProblemData.begin"
                        label="Picker without buttons"
                        prepend-icon="mdi-event"
                        readonly
                        v-on="on"
                      ></v-text-field>
                    </template>
                    <v-date-picker v-model="dialogProblemData.begin" @input="beginpicker = false"></v-date-picker>
                  </v-menu>
                </v-col>
                <v-col>
                  <v-menu
                    v-model="eindpicker"
                    :close-on-content-click="false"
                    :nudge-right="40"
                    transition="scale-transition"
                    offset-y
                    min-width="290px"
                  >
                    <template v-slot:activator="{ on }">
                      <v-text-field
                        v-model="dialogProblemData.eind"
                        label="Picker without buttons"
                        prepend-icon="mdi-event"
                        readonly
                        v-on="on"
                      ></v-text-field>
                    </template>
                    <v-date-picker v-model="dialogProblemData.eind" @input="eindpicker = false"></v-date-picker>
                  </v-menu>
                </v-col>
              </v-row>
              <v-row>
                <v-select
                  v-show="dialogProblemData.type"
                  :items="['74400008']"
                  :label="dialogProblemData.type"
                  v-model="dialogProblemData.naam"
                  dense
                  outlined
                ></v-select>
              </v-row>
            </v-container>
            <small>*verplichte velden</small>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="blue darken-1" text @click="dialogProblem = false">Close</v-btn>
            <v-btn color="blue darken-1" text @click="saveDialogProblem()">Save</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-container>

  </div>
</template>

<script>
export default {
  data() {
    return {
      dialogDecursus: false,
      dialogDeleteDecursus: false,
      dialogDeleteDecursusData: {
        decursusId: null,
        patientId: this.$store.state.Epd.currentPatient.id
      },
      dialogProblem: false,
      dialogProblemData: {},
      dialog2: false,
      dialog3: false,
      eindpicker: false,
      beginpicker: false,
      problemTypes: [
        'Diagnose','Symptoom','Klacht','Functionele beperking','Complicatie'
      ]
    }
  },
  methods: {
    setCurrentPatient: function (event) {
      this.$store.state.currentPatient = event
      this.$store.dispatch('Epd/getDecursus',this.$store.state.Epd.currentPatient.id)
    },
    addNewDecursus: function(){
      this.$store.dispatch('Epd/newDecursus',this.$store.state.Epd.currentPatient.id)
    },
    deleteDecursusDialog: function(decursusId) {
      this.dialogDeleteDecursus = true
      this.dialogDeleteDecursusData.decursusId = decursusId
    },
    deleteDecursus: function(){
      this.$store.dispatch('Epd/deleteDecursus',this.dialogDeleteDecursusData.decursusId)
      this.dialogDeleteDecursus = false
    },
    openEditDialogDecursus: function(decursusId) {
      // Empty data object for decursus dialog
      this.dialogDecursusData = {}
      // Get data
      this.$store.dispatch('Epd/getDecursusDetail',decursusId)
      // Open dialog
      this.dialogDecursus = true
    },
    openAddDialogProblem: function(decursusId) {
      // Empty data object for decursus dialog
      this.dialogProblemData = {'decursusId':decursusId}
      // Open dialog
      this.dialogProblem = true
    },
    saveDialogDecursus: function(){
      // Close decursus dialog
      this.dialogDecursus = false
      var payload = {
        'action':'patch',
        'decursus':this.dialogDecursusData
        }
      // Dispatch post
      this.$store.dispatch('Epd/postDecursus',payload)
      this.$store.dispatch('Epd/getDecursus',this.$store.state.Epd.currentPatient.id)
      // Clear decursus dialog data
      this.dialogDecursusData = {}
    },
    saveDialogProblem: function(){
      // Close decursus dialog
      this.dialogProblem = false
      var payload = {
        'action':'new',
        'patientId':this.$store.state.Epd.currentPatient.id,
        'problem':this.dialogProblemData
        }
      // Dispatch post
      this.$store.dispatch('Epd/postProblem',payload)
      this.$store.dispatch('Epd/getDecursus',this.$store.state.Epd.currentPatient.id)
      // Clear decursus dialog data
      this.dialogProblemData = {}
    }
  },
  computed: {
    currentPatient(){
      return this.$store.state.Epd.currentPatient;
    },
    currentPatientDecursus(){
      return this.$store.state.Epd.currentPatientDecursus;
    },
    dialogDecursusData(){
      return this.$store.state.Epd.dialogDecursusData;
    }
  }
}
</script>