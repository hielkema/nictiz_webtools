<template>
  <div>
    <v-card-title>
      Resultaten
    <v-text-field
        v-model="search"
        label="Zoek binnen resultaten"
        hide-details
        autofocus
        dense
      ></v-text-field>
    </v-card-title>
    <v-data-table dense multi-sort :headers="headers" :items="searchResults" :search="search" item-key="id+comment+user"></v-data-table>
  </div>
</template>

<script>
export default {
  data() {
    return {
      search: '',
      headers: [
        { 'text' : 'ID', value: 'id', filterable: true },
        { 'text' : 'FSN', value: 'fsn', filterable: true },
        { 'text' : 'Status', value: 'status' },
        { 'text' : 'User', value: 'author' },
        { 'text' : 'Folder', value: 'folder' },
        { 'text' : 'Commentaar', value: 'comment' },
      ]
    }
  },
  methods: {
  },
  computed: {
    searchResults(){
      return this.$store.state.TermspaceComments.results;
    }
  }
}
</script>