<template>
  <div>
    
    <v-card>
      <v-card-title>
        <v-text-field
          v-model="search"
          label="Search"
          single-line
          hide-details
        ></v-text-field>
      </v-card-title>
      <v-data-table 
      :headers="headers"
      :items="patients"
      :items-per-page="5"
      :search="search"
      multi-sort
      dense
      class="elevation-1"
      >
      </v-data-table>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'PatientList',
  // props: ["patients"],
  data() {
    return {
      search: '',
      headers: [
          {text:'ID',value:'id'},
          {text:'Achternaam', value:'surname',filterable:true},
          {text:'Opgenomen',value:'admitted',filterable:true}
        ]
    }
  }
}
</script>