<template>
  <div v-if="user.groups.includes('mapping | access')">
    <v-card 
      class="ma-1"
      max-width="500"
    >   
      <v-simple-table
        dense
      >
        <tbody>
          <tr>
            <th>
              Zoek binnen resultaten
            </th>
            <td>
              <v-text-field
                v-model="search"
                label="Zoek binnen resultaten"
                hide-details
                autofocus
                clearable
                dense
              ></v-text-field>
            </td>
          </tr>
          <tr
            v-for="header in headers"
            :key="header.text"
          >
            <th v-if="filters.hasOwnProperty(header.value)">
              {{header.text}}
            </th>
            <td v-if="filters.hasOwnProperty(header.value)" class="text-left">
              <v-select flat dense hide-details small multiple clearable :items="columnValueList(header.value)" v-model="filters[header.value]">     
              </v-select>
            </td>
          </tr>
          <tr>
            <th>
              Group by
            </th>
            <td>
              <v-select flat dense hide-details small :items="groupByList" v-model="groupBy">
              </v-select>
            </td>
          </tr>
        </tbody>
      </v-simple-table>
    </v-card>

    <v-spacer></v-spacer>
      
    <v-card class="ma-1">
      <v-data-table 
        :footer-props="pagination" 
        :group-by="groupBy"
        fixed-header
        dense 
        multi-sort 
        :headers="headers" 
        :items="filteredResults" 
        :search="search" 
        item-key="id+comment+user">
        
        <template v-slot:item.task_id="{ item }">
          <a :href="'https://termservice.test-nictiz.nl/mapping/project/' + item.project_id + '/task/' + item.task_id" target="_blank">{{ item.task_id }}</a>
        </template>
        
        </v-data-table>
    </v-card>
  </div>
</template>

<script>
export default {
  data() {
    return {
      search: '',
      groupBy: null,
      headers: [
        { 'text' : 'TaakID', value: 'task_id', filterable: true },
        { 'text' : 'Project', value: 'project', filterable: true },
        { 'text' : 'Component', value: 'component_title' },
        { 'text' : 'Status', value: 'status' },
        { 'text' : 'User', value: 'user' },
        { 'text' : 'Commentaar', value: 'comment' },
      ],
      pagination: {
        "items-per-page-options": [5,10,25,50]
      },
      filters: {
        user: [],
        project: [],
        status: [],
      }
    }
  },
  methods: {
    columnValueList(val) {
      return this.$store.state.MappingComments.results.map(d => d[val]).sort()
    }
  },
  computed: {
    searchResults(){
      return this.$store.state.MappingComments.results;
    },
    filteredResults() {
      return this.$store.state.MappingComments.results.filter(d => {
        return Object.keys(this.filters).every(f => {
          return this.filters[f].length < 1 || this.filters[f].includes(d[f])
        })
      })
    },
    groupByList(){
      const result = this.headers
      // result.push('Niet groeperen')
      return result
    }
  }
}
</script>