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