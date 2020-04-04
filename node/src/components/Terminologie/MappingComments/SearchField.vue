<template>
  <div v-if="user.groups.includes('mapping | access')">
    <form v-on:submit.prevent>
    <v-card
      class="ma-1">
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
      <v-card-text>Je kan zoeken op tekst in het commentaar of op het Taak ID.<br>Tip: Zoeken op Taak ID geeft alle commentaren van de taak - handig voor een overzicht.</v-card-text>
    </v-card>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchTerm: '',
      loading: false,
    }
  },
  methods: {
    searchForThis: function (searchTerm) {
      searchTerm = searchTerm.replace(/#/g, '%23');
      this.$store.dispatch('MappingComments/getResults',searchTerm)
    }
  },
  computed: {
    user(){
      return this.$store.state.userData
    }
  }
}
</script>