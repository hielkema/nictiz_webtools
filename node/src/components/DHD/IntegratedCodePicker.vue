<template>
  <div>
    <v-card>
        <v-subheader>Zoeken</v-subheader>
        <v-form>
            <v-text-field
                label="Zoekterm"
                v-model="searchterm"></v-text-field>
            <v-btn
                color="success"
                v-on:click="search(searchterm)">
                Zoek
            </v-btn>
        </v-form>
        <br>
        Filters:<br>
        <v-btn v-on:click="setDTFilter(true)">Aan</v-btn> Toon alleen Diagnosethesaurus resultaten, termen met Diagnosethesaurus-koppeling, of termen met kinderen met een Diagnosethesaurus-koppeling<br>
        <v-btn v-on:click="setDTFilter(false)">Uit</v-btn> Toon alle resultaten
    </v-card>
    <v-row>
        <v-col cols=6>
            <v-card>
                <v-subheader>Zoekresultaten: searchResultsFiltered na filteren - ({{searchResults.results_returned}} opgehaald / {{searchResults.results_total}} gevonden)</v-subheader>
                <v-list v-if="loading.searchResults">
                    <p>Loading</p>
                </v-list>
                <v-list v-else>
                    <v-list-item
                        v-for="result in searchResultsFiltered"
                        v-bind:key="result.id"
                        v-on:click="fetchConcept(result.id)"
                        link>
                        <v-list-item-content>
                            <v-list-item-title text-color="secondary"><v-icon small v-if="result.equivalent">mdi-link-variant</v-icon>{{result.title}}</v-list-item-title>
                            <v-list-item-subtitle>{{result.codesystem}}<span v-if="result.dt_in_descendants && hide_no_dt == false"> - Heeft DT koppeling, of kinderen met koppeling</span></v-list-item-subtitle>
                            <!-- {{eq.codesystem}}: {{eq.title}} -->
                            
                        </v-list-item-content>
                    </v-list-item>
                </v-list>
            </v-card>
        </v-col>

        <v-col cols=6>
            <v-card>
                <v-subheader>Parents (parentsFiltered na filteren /parents zonder filter)</v-subheader>
                <v-list v-if="loading.parents">
                    <p>Loading</p>
                </v-list>
                <v-list v-else>
                    <v-list-item
                        v-for="result in parentsFiltered"
                        v-bind:key="result.id"
                        v-on:click="fetchConcept(result.id)"
                        link>
                        <v-list-item-content>
                            <v-list-item-title text-color="secondary"><v-icon small v-if="result.equivalent">mdi-link-variant</v-icon>{{result.title}}</v-list-item-title>
                            <v-list-item-subtitle>{{result.codesystem}} (children: {{result.children}} / DT in children: {{result.dt_in_descendants}})</v-list-item-subtitle>                            
                        </v-list-item-content>
                    </v-list-item>
                </v-list>
            </v-card>
            <v-card>
                <v-subheader>Component</v-subheader>
                <v-list v-if="loading.concept">
                    <p>Loading</p>
                </v-list>
                <v-list v-else>
                    <v-list-item
                        v-for="(value, key) in currentConcept"
                        v-bind:key="key">
                        <v-list-item-content v-if="key != 'equivalent'">
                            <v-list-item-title><b>{{key}}</b></v-list-item-title>
                            <v-list-item-subtitle>{{value}}</v-list-item-subtitle>
                        </v-list-item-content>

                        <!-- Equivalentie in DT indien aanwezig -->
                        <v-list-item-content v-if="(key == 'equivalent') & (value != false)">
                            <v-list-item-title><b>Mapping</b></v-list-item-title>
                            <v-list-item-subtitle>
                                <!-- List of mappings -->
                                <v-list>
                                    <v-list-item
                                        v-for="target in value"
                                        v-bind:key="target.id"
                                        v-on:click="fetchConcept(target.id)"
                                        link>
                                        <v-list-item-content>
                                            <v-list-item-title text-color="secondary"><v-icon small v-if="target.equivalent">mdi-link-variant</v-icon>{{target.title}}</v-list-item-title>
                                            <v-list-item-subtitle>{{target.codesystem}}</v-list-item-subtitle>
                                        </v-list-item-content>
                                    </v-list-item>
                                </v-list>


                            </v-list-item-subtitle>
                        </v-list-item-content>
                        <!-- Handle situations where mapping is not available -->
                        <v-list-item-content v-if="(key == 'equivalent') & (value == false)">
                            <v-list-item-title><b>Mapping</b></v-list-item-title>
                            <v-list-item-subtitle>
                                Geen mapping aanwezig
                            </v-list-item-subtitle>
                        </v-list-item-content>


                    </v-list-item>
                </v-list>
            </v-card>
            <v-card>
                <v-subheader>Children (childrenFiltered na filteren /children zonder filter)</v-subheader>
                <v-list v-if="loading.children">
                    <p>Loading</p>
                </v-list>
                <v-list v-else>
                    <v-list-item
                        v-for="result in childrenFiltered"
                        v-bind:key="result.id"
                        v-on:click="fetchConcept(result.id)"
                        link>
                        <v-list-item-content>
                            <v-list-item-title text-color="secondary"><v-icon small v-if="result.equivalent">mdi-link-variant</v-icon>{{result.title}}</v-list-item-title>
                            <v-list-item-subtitle>{{result.codesystem}} (children: {{result.children}} / DT in children {{result.dt_in_descendants}})</v-list-item-subtitle>                            
                        </v-list-item-content>
                    </v-list-item>
                </v-list>
            </v-card>
        </v-col>
    </v-row>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchterm: '',
      hide_no_dt: true,
    }
  },
  methods: {
    search: function(term) {
        this.$store.dispatch('IntegratedCodePicker/search',term)
    },
    fetchConcept: function(conceptid) {
        this.$store.dispatch('IntegratedCodePicker/getConcept',conceptid)
        this.$store.dispatch('IntegratedCodePicker/getParents',conceptid)
        this.$store.dispatch('IntegratedCodePicker/getChildren',conceptid)
    },
    setDTFilter: function(value) {
        this.hide_no_dt = value;
    }
  },
  computed: {
    loading(){
        return this.$store.state.IntegratedCodePicker.loading;
    },
    searchResults(){
        return this.$store.state.IntegratedCodePicker.searchResults;
    },
    searchResultsFiltered(){
        if((this.searchResults.results.length > 0) && (this.hide_no_dt == true)){
            return this.searchResults.results.filter(function(result) {
                return result.dt_in_descendants == true;
            });
        }else{
            return this.searchResults.results;
        }
    },
    currentConcept(){
        return this.$store.state.IntegratedCodePicker.currentConcept;
    },
    children(){
        return this.$store.state.IntegratedCodePicker.children;
    },
    childrenFiltered(){
        if(this.hide_no_dt == true){
            return this.children.filter(function(result) {
                return result.dt_in_descendants == true;
            });
        }else{
            return this.children
        }
    },
    parents(){
        return this.$store.state.IntegratedCodePicker.parents;
    },
    parentsFiltered(){
        if(this.hide_no_dt == true){
            return this.parents.filter(function(result) {
                return result.dt_in_descendants == true;
            });
        }else{
            return this.parents
        }
    },
  }
}
</script>