<template>
  <div>
    <v-card>
      <v-card-title>
        <span class="headline">Zoeken</span>
      </v-card-title>
      <v-card-text>
        <v-container>
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
        </v-container>
      </v-card-text>
      <v-card-actions>
        <v-btn color="blue" @click="searchForThis(searchTerm)">Zoek</v-btn>
      </v-card-actions>
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
      console.error(process.env.APIURL)
      this.$store.dispatch('TermspaceComments/getResults',searchTerm)
    }
  },
  computed: {
  }
}
</script>