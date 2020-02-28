<template>
  <div>
    <form v-on:submit.prevent>
    <v-card>
      <v-card-title>
        <span class="headline">Zoeken</span>
      </v-card-title>
      <v-card-text>
          <v-row>
              <v-text-field
                name="Zoekterm"
                filled
                dense
                label="Zoekterm*"
                persistent-label
                v-model="searchTerm"
              ></v-text-field>
          </v-row>
      </v-card-text>
      <v-card-actions>
        <v-btn color="blue" type="submit" @click="searchForThis(searchTerm)">Zoek</v-btn>
      </v-card-actions>
    </v-card>
    </form>

    <v-card
      class="ma-1">
      <v-card-text>Je kan zoeken op tekst in het commentaar, gebruiker, werklijst, status, concept ID of FSN.<br>Tip: Zoeken op FSN geeft alle commentaren van de taak - handig voor een overzicht.</v-card-text>
    </v-card>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchTerm: '',
    }
  },
  methods: {
    searchForThis: function (searchTerm) {
      this.$store.dispatch('TermspaceComments/getResults',searchTerm)
    }
  },
  computed: {
  }
}
</script>